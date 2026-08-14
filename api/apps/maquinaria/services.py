from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import EdoMaquina, HistorialEstadoMaquina, Maquina

# Transiciones permitidas — coincide con tu diagrama:
# OPERA -> FALLO (se reporta falla) / DESHA (se deshabilita manualmente)
# FALLO -> MANTE (técnico inicia la orden) / DESHA (se da de baja aunque siga fallando)
# MANTE -> ESPER (técnico cierra la orden, reparada, falta validar) / DESHA (se da de baja a media reparación)
# ESPER -> OPERA (admin valida) / FALLO (se detecta que en realidad sigue fallando) / DESHA (se da de baja en vez de validar)
# DESHA -> OPERA (admin reactiva)
# "Deshabilitar" es una decisión administrativa (baja, venta, obsolescencia,
# accidente, etc.) que puede tomarse en cualquier momento del ciclo de vida
# de la máquina, sin importar en qué estado se encuentre en ese momento.
TRANSICIONES_VALIDAS = {
    "OPERA": {"FALLO", "DESHA"},
    "FALLO": {"MANTE", "DESHA"},
    "MANTE": {"ESPER", "DESHA"},
    "ESPER": {"OPERA", "FALLO", "DESHA"},
    "DESHA": {"OPERA"},
}

# Salir de OPERA hacia estos estados es lo único que "cierra" un periodo
# de operación -> dispara el INSERT en REGISTRO_OPS -> trigger de MTBF.
ESTADOS_QUE_DETIENEN_OPERACION = {"FALLO", "DESHA"}


@transaction.atomic
def cambiar_estado_maquina(maquina_codigo, nuevo_estado, referencia_tipo=None, referencia_id=None, forzar=False):
    """Punto único para cambiar Maquina.estado_maquina. Todo lo automático
    (fallas/mantenimiento/monitoreo) y lo manual (endpoints de views.py)
    pasan siempre por aquí, para que HISTORIAL_ESTADO_MAQUINA y
    REGISTRO_OPS (y en cascada MTBF/MTTR/Disponibilidad vía los triggers
    de triggers2.sql) queden consistentes sin importar el origen del cambio.

    Recibe el codigo (string) de la máquina, NUNCA un objeto Maquina:
    fallas.Maquina, monitoreo.Maquina (importado de fallas) y maquinaria.Maquina
    son clases Django distintas sobre la misma tabla MAQUINA y no son
    intercambiables entre sí (Django valida el tipo al asignar un FK).
    """
    maquina = Maquina.objects.select_for_update().get(codigo=maquina_codigo)
    estado_anterior = maquina.estado_maquina_id

    if estado_anterior == nuevo_estado:
        return maquina  # no-op: evita historial y triggers duplicados

    if not forzar:
        permitidos = TRANSICIONES_VALIDAS.get(estado_anterior, set())
        if nuevo_estado not in permitidos:
            nombres = dict(EdoMaquina.objects.values_list("codigo", "nombre"))
            nombre_anterior = nombres.get(estado_anterior, estado_anterior)
            nombre_nuevo = nombres.get(nuevo_estado, nuevo_estado)
            raise ValidationError(f"Transición no permitida: {nombre_anterior} -> {nombre_nuevo}.")

    ahora = timezone.localtime()

    if estado_anterior == "OPERA" and nuevo_estado in ESTADOS_QUE_DETIENEN_OPERACION:
        _registrar_horas_operacion(maquina, ahora)

    HistorialEstadoMaquina.objects.create(
        maquina=maquina,
        estado_anterior_id=estado_anterior,
        estado_nuevo_id=nuevo_estado,
        referencia_tipo=referencia_tipo,
        referencia_id=referencia_id,
    )
    maquina.estado_maquina_id = nuevo_estado
    maquina.save(update_fields=["estado_maquina"])

    if nuevo_estado == "OPERA" and maquina.requiere_revision_preventiva:
        maquina.requiere_revision_preventiva = False
        maquina.save(update_fields=["requiere_revision_preventiva"])

    return maquina


def _registrar_horas_operacion(maquina, ahora):
    """INSERT en REGISTRO_OPS -> dispara tg_actualizar_mtbf_registroops
    (ya existe en triggers2.sql, no se toca).

    Nota: no se reutiliza monitoreo.services.registrar_horas_operacion()
    aunque hace lo mismo, porque esa función espera un objeto Maquina
    completo (de fallas.models) y aquí solo tenemos maquinaria.Maquina.
    Se usa maquina_id=... directo para no cruzar clases distintas de
    Maquina (ver docstring de cambiar_estado_maquina más arriba)."""
    from datetime import datetime, time
    from apps.monitoreo.models import RegistroOps

    ultimo_inicio = (
        HistorialEstadoMaquina.objects.filter(maquina=maquina, estado_nuevo_id="OPERA")
        .order_by("-fecha")
        .values_list("fecha", flat=True)
        .first()
    )
    # Horas con precisión real (total_seconds/3600), igual que tiempoParo en
    # mantenimiento: el cálculo anterior por .days*24 truncaba a días completos
    # y cualquier periodo < 24 h daba 0 -> nunca se insertaba en REGISTRO_OPS
    # -> el MTBF se quedaba en NULL para siempre.
    inicio_dt = ultimo_inicio or timezone.make_aware(datetime.combine(maquina.fechainstalacion, time.min))
    horas = max(int((ahora - inicio_dt).total_seconds() / 3600), 0)
    if horas > 0:
        RegistroOps.objects.create(
            maquina_id=maquina.codigo, fechaInicio=inicio_dt.date(), fechaFin=ahora.date(), horasOperacion=horas,
        )