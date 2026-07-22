from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.fallas.models import EstadoReporte, ReporteFalla, TipoFalla, TipoSeveridad
from apps.usuarios.models import Trabajador

from .models import EstadoOrden, LecturaSensor, OrdenMantenimiento, TipoMantenimiento

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
