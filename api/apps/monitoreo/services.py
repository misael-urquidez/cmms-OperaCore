import random

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.fallas.models import EstadoReporte, ReporteFalla, TipoFalla, TipoSeveridad
from apps.usuarios.models import Trabajador

from .models import EstadoOrden, LecturaSensor, OrdenMantenimiento, RegistroOps, TipoMantenimiento


LECTURAS_TENDENCIA = 5
MINIMO_FUERA_UMBRAL = 3


def evaluar_tendencia(maquina):
    """Actualiza y devuelve la bandera preventiva; no crea reportes ni órdenes."""
    lecturas = list(
        LecturaSensor.objects.filter(maquina=maquina)
        .order_by("-timestamp")[:LECTURAS_TENDENCIA]
    )
    fuera_de_rango = sum(lectura.vibracion > maquina.umbral_vibracion for lectura in lecturas)
    requiere_revision = len(lecturas) == LECTURAS_TENDENCIA and fuera_de_rango >= MINIMO_FUERA_UMBRAL
    if maquina.requiere_revision_preventiva != requiere_revision:
        maquina.requiere_revision_preventiva = requiere_revision
        maquina.save(update_fields=["requiere_revision_preventiva"])
    return requiere_revision


def _crear_falla_y_orden_por_golpe(maquina):
    """Crea una alerta correctiva con catálogos estándar de OperaCore."""
    trabajador = Trabajador.objects.filter(actividad=True).order_by("numeroNomina").first()
    tipo_falla = TipoFalla.objects.order_by("numeroRegistro").first()
    severidad = TipoSeveridad.objects.filter(codigo="CRITI").first()
    estado_reporte = EstadoReporte.objects.filter(codigo="ABIER").first()
    tipo_mantenimiento = TipoMantenimiento.objects.filter(codigo="CORRE").first()
    estado_orden = EstadoOrden.objects.filter(codigo="SOLIC").first()
    if not all((trabajador, tipo_falla, severidad, estado_reporte, tipo_mantenimiento, estado_orden)):
        raise ValidationError("Faltan catálogos o un trabajador activo para crear la alerta automática.")

    ahora = timezone.localtime()
    reporte = ReporteFalla.objects.create(
        asunto="Golpe detectado por monitoreo",
        fechaCreacion=ahora.date(), horaCreacion=ahora.time(),
        causaRaiz="Pendiente de diagnóstico: golpe detectado por sensor.",
        descripcion="Reporte generado automáticamente por el módulo de monitoreo.",
        maquina=maquina, trabajador=trabajador, tipo_falla=tipo_falla,
        tipo_severidad=severidad, estado_reporte=estado_reporte,
    )
    folio = f"OM-A{reporte.numeroRegistro:010d}"  # 15 caracteres, único por reporte.
    OrdenMantenimiento.objects.create(
        folio=folio, descripcion="Inspección correctiva por golpe detectado.",
        fechaCreacion=ahora.date(), horaCreacion=ahora.time(), maquina=maquina,
        trabajador=trabajador, reporte_falla=reporte,
        tipo_mantenimiento=tipo_mantenimiento, estado_orden=estado_orden,
    )

    from apps.maquinaria.services import cambiar_estado_maquina
    cambiar_estado_maquina(maquina.codigo, "FALLO", "reporte_falla", str(reporte.numeroRegistro))

    return reporte


@transaction.atomic
def registrar_lectura(maquina, origen, vibracion, golpe=False, temperatura=None):
    """Punto único para lecturas manuales, simuladas y futuras lecturas IoT."""
    if origen not in dict(LecturaSensor.ORIGENES):
        raise ValidationError({"origen": "Origen no válido."})
    lectura = LecturaSensor.objects.create(
        maquina=maquina, timestamp=timezone.now(), origen=origen,
        vibracion=vibracion, golpe=golpe, temperatura=temperatura,
    )
    reporte = _crear_falla_y_orden_por_golpe(maquina) if golpe else None
    requiere_revision = evaluar_tendencia(maquina) if not golpe else maquina.requiere_revision_preventiva
    return lectura, reporte, requiere_revision


def generar_lectura_simulada(maquina, golpe_probabilidad=0.02):
    """Genera una lectura simulada realista para una máquina.
    Usado por el comando `simular_lecturas` y por el botón
    'Generar lectura simulada ahora' del panel de monitoreo."""
    fuera_de_rango = random.random() < 0.12
    vibracion = (
        random.uniform(maquina.umbral_vibracion * 1.05, maquina.umbral_vibracion * 1.6)
        if fuera_de_rango else random.uniform(0.1, maquina.umbral_vibracion * 0.85)
    )
    golpe = random.random() < golpe_probabilidad
    return registrar_lectura(
        maquina=maquina, origen=LecturaSensor.ORIGEN_SIMULADO,
        vibracion=round(vibracion, 3), golpe=golpe,
        temperatura=round(random.uniform(20, 45), 1),
    )


def registrar_horas_operacion(maquina, fechaInicio, fechaFin, horasOperacion):
    """Registra un periodo de operación (INSERT en REGISTRO_OPS).
    Esto es lo que en realidad mueve el MTBF: el trigger
    `tg_actualizar_mtbf_registroops` recalcula el MTBF de la máquina
    y lo guarda en el periodo vigente de INDICADOR. El MTBF/MTTR/
    disponibilidad en sí NUNCA se escriben a mano; solo se alimentan
    los datos de origen (horas operadas, fallas, cierres de orden) y
    los triggers hacen el cálculo."""
    return RegistroOps.objects.create(
        maquina=maquina, fechaInicio=fechaInicio, fechaFin=fechaFin,
        horasOperacion=horasOperacion,
    )



def registrar_reparacion_manual(maquina, horas_reparacion):
    """Equivalente de registrar_horas_operacion() pero para el MTTR: crea
    un REPORTE_FALLA ya resuelto (con tiempoParo fijado a mano) y una
    ORDEN_MANTENIMIENTO ya cerrada, y deja que tg_actualizar_mttr_orden haga
    el cálculo -- el MTTR nunca se escribe a mano.

    A propósito NO llama a cambiar_estado_maquina(): es un dato histórico
    de prueba/demo, no debe mover el estado en vivo de la máquina ni
    tropezar con el flujo automático de fallas/órdenes."""
    from apps.mantenimiento.models import OrdenMantenimiento as OrdenMantenimientoCompleta

    trabajador = Trabajador.objects.filter(actividad=True).order_by("numeroNomina").first()
    severidad = TipoSeveridad.objects.filter(codigo="CRITI").first()
    estado_reporte = EstadoReporte.objects.filter(codigo="RESUE").first()
    tipo_mantenimiento = TipoMantenimiento.objects.filter(codigo="CORRE").first()
    estado_orden = EstadoOrden.objects.filter(codigo="CERRA").first()
    if not all((trabajador, severidad, estado_reporte, tipo_mantenimiento, estado_orden)):
        raise ValidationError("Faltan catálogos o un trabajador activo para registrar la reparación manual.")

    ahora = timezone.localtime()
    reporte = ReporteFalla.objects.create(
        asunto="Reparación registrada manualmente (demo/prueba)",
        fechaCreacion=ahora.date(), horaCreacion=ahora.time(),
        causaRaiz="Registro manual para pruebas o demostración.",
        descripcion="Generado desde el panel de monitoreo para alimentar el MTTR sin esperar horas reales.",
        maquina=maquina, trabajador=trabajador,
        tipo_severidad=severidad, estado_reporte=estado_reporte,
        tiempoParo=horas_reparacion,
    )
    folio = f"OM-M{reporte.numeroRegistro:010d}"
    OrdenMantenimientoCompleta.objects.create(
        folio=folio, descripcion="Reparación manual (alimenta MTTR).",
        fechacreacion=ahora.date(), horacreacion=ahora.time(), maquina_id=maquina.codigo,
        trabajador_id=trabajador.numeroNomina, reporte_falla_id=reporte.numeroRegistro,
        tipo_mantenimiento_id=tipo_mantenimiento.codigo, estado_orden_id="EJECU",
    )
    # Se cierra con un UPDATE real y aparte del INSERT de arriba, porque
    # tg_actualizar_mttr_orden es AFTER UPDATE (solo dispara cuando
    # fechaCierre pasa de NULL a no-NULL).
    OrdenMantenimientoCompleta.objects.filter(pk=folio).update(
        fechacierre=ahora.date(), horacierre=ahora.time(), estado_orden_id="CERRA",
    )
    return reporte