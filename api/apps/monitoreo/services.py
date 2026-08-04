import random

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.fallas.models import EstadoReporte, ReporteFalla, TipoSeveridad
from apps.usuarios.models import Trabajador

from .models import EstadoOrden, LecturaSensor, OrdenMantenimiento, RegistroOps, TipoMantenimiento


LECTURAS_TENDENCIA = 5
MINIMO_FUERA_UMBRAL = 3
GOLPES_PARA_FALLO = 3


def evaluar_tendencia(maquina):
    """Actualiza y devuelve la bandera preventiva. Es "sticky": esta función
    solo puede ENCENDERLA. Apagarla requiere una acción explícita de
    reparación/validación (ver limpiar_revision_preventiva)."""
    lecturas = list(
        LecturaSensor.objects.filter(maquina=maquina)
        .order_by("-timestamp")[:LECTURAS_TENDENCIA]
    )
    fuera_de_rango = sum(lectura.vibracion > maquina.umbral_vibracion for lectura in lecturas)
    requiere_revision = len(lecturas) == LECTURAS_TENDENCIA and fuera_de_rango >= MINIMO_FUERA_UMBRAL

    if requiere_revision and not maquina.requiere_revision_preventiva:
        maquina.requiere_revision_preventiva = True
        maquina.save(update_fields=["requiere_revision_preventiva"])

    return maquina.requiere_revision_preventiva


def limpiar_revision_preventiva(maquina):
    """Apaga la bandera preventiva a propósito (reparación/validación)."""
    if maquina.requiere_revision_preventiva:
        maquina.requiere_revision_preventiva = False
        maquina.save(update_fields=["requiere_revision_preventiva"])


def _procesar_golpe(maquina):
    """Golpe detectado por el sensor (manual/simulado/iot). A propósito NO
    crea ReporteFalla ni OrdenMantenimiento -- eso requeriría catálogos
    completos y para un golpe crudo del sensor no hay diagnóstico real
    todavía. Solo: (1) prende la alerta de revisión, y (2) si ya se
    acumularon GOLPES_PARA_FALLO golpes desde que la máquina quedó
    operativa por última vez, la pasa a FALLO."""
    from apps.maquinaria.models import HistorialEstadoMaquina
    from apps.maquinaria.services import cambiar_estado_maquina

    if not maquina.requiere_revision_preventiva:
        maquina.requiere_revision_preventiva = True
        maquina.save(update_fields=["requiere_revision_preventiva"])

    if maquina.estado_maquina != "OPERA":
        return  # ya no está operando; no tiene caso seguir contando golpes

    desde = (
        HistorialEstadoMaquina.objects.filter(maquina_id=maquina.codigo, estado_nuevo_id="OPERA")
        .order_by("-fecha")
        .values_list("fecha", flat=True)
        .first()
    )
    golpes = LecturaSensor.objects.filter(maquina=maquina, golpe=True)
    if desde:
        golpes = golpes.filter(timestamp__gte=desde)
    total_golpes = golpes.count()

    if total_golpes >= GOLPES_PARA_FALLO:
        try:
            cambiar_estado_maquina(maquina.codigo, "FALLO", "golpe_sensor", None)
        except ValidationError:
            pass  # transición no permitida justo ahora; la alerta ya quedó activa


@transaction.atomic
def registrar_lectura(maquina, origen, vibracion, golpe=False, temperatura=None):
    """Punto único para lecturas manuales, simuladas y IoT."""
    if origen not in dict(LecturaSensor.ORIGENES):
        raise ValidationError({"origen": "Origen no válido."})
    lectura = LecturaSensor.objects.create(
        maquina=maquina, timestamp=timezone.now(), origen=origen,
        vibracion=vibracion, golpe=golpe, temperatura=temperatura,
    )
    if golpe:
        _procesar_golpe(maquina)
        requiere_revision = True
    else:
        requiere_revision = evaluar_tendencia(maquina)
    return lectura, None, requiere_revision


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


def recalcular_mtbf_maquina(maquina_codigo):
    """Recalcula el MTBF de una máquina desde cero (misma lógica que
    tg_actualizar_mtbf_registroops) y actualiza el periodo vigente
    de INDICADOR. Se usa después de editar/eliminar un REGISTRO_OPS
    para que el indicador refleje el cambio."""
    from django.db.models import Count, Sum
    from apps.fallas.models import ReporteFalla
    from .models import Indicador

    total_horas = RegistroOps.objects.filter(
        maquina_id=maquina_codigo
    ).aggregate(total=Sum("horasOperacion"))["total"] or 0

    total_fallas = ReporteFalla.objects.filter(
        maquina_id=maquina_codigo
    ).count()

    if total_fallas > 0:
        nuevo_mtbf = total_horas / total_fallas
    else:
        nuevo_mtbf = None

    periodo = Indicador.objects.filter(
        maquina_id=maquina_codigo, fechaFin__isnull=True
    ).first()

    if periodo:
        periodo.mtbf = nuevo_mtbf
        periodo.save(update_fields=["mtbf"])
    else:
        Indicador.objects.create(
            maquina_id=maquina_codigo,
            fechaInicio=timezone.localdate(),
            mtbf=nuevo_mtbf,
        )

    return nuevo_mtbf



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
    limpiar_revision_preventiva(maquina)
    return reporte


def reparar_via_iot(maquina):
    """Resuelve de un toque la falla activa de esta máquina desde IoT."""
    falla = ReporteFalla.objects.filter(maquina=maquina).exclude(
        estado_reporte_id__in=["RESUE", "CERRA", "CANCE"]
    ).order_by("-fechaCreacion", "-horaCreacion").first()
    if falla is None:
        return None

    estado_resuelto = EstadoReporte.objects.filter(codigo="RESUE").first()
    if not estado_resuelto:
        raise ValidationError("Falta el catálogo de estado de reporte RESUE.")
    falla.estado_reporte = estado_resuelto
    falla.fechaResolucion = timezone.localdate()
    falla.save(update_fields=["estado_reporte", "fechaResolucion"])

    estado_cerrado = EstadoOrden.objects.filter(codigo="CERRA").first()
    if estado_cerrado:
        OrdenMantenimiento.objects.filter(reporte_falla=falla).update(estado_orden=estado_cerrado)

    from apps.maquinaria.services import cambiar_estado_maquina
    cambiar_estado_maquina(maquina.codigo, "OPERA", "reporte_falla", str(falla.numeroRegistro), forzar=True)
    limpiar_revision_preventiva(maquina)
    return falla