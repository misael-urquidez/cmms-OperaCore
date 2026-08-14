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

@transaction.atomic
def cambiar_estado_maquina(maquina_codigo, nuevo_estado, referencia_tipo=None, referencia_id=None, forzar=False):
    """Punto único para cambiar Maquina.estado_maquina. Todo lo automático
    (fallas/mantenimiento/monitoreo) y lo manual (endpoints de views.py)
    pasan siempre por aquí, para que HISTORIAL_ESTADO_MAQUINA quede
    consistente sin importar el origen del cambio. Las horas de operación
    se registran SIEMPRE a mano en REGISTRO_OPS (módulo Monitoreo); este
    cambio de estado ya no las auto-genera.

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
