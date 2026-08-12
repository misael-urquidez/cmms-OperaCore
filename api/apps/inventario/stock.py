"""Mecanica de stock de herramientas.

REFACCION tiene triggers en la BD que mantienen REFACCION.stock = SUMA de
ESTADO_REFACCION.cantidad y que siembran la fila DISPO al crear. HERRAMIENTA
no tiene triggers, asi que estas funciones replican esa invariante en Python:

    HERRAMIENTA.stock  = SUMA(ESTADO_HERRAMIENTA.cantidad)
    DISPO (disponible) = unidades listas para asignarse
    ENUSO (en uso)     = unidades asignadas a ordenes de mantenimiento

Reglas:
  * Subir stock: el delta entra como DISPO.
  * Bajar stock: se rechaza si la suma de estados NO disponibles es mayor
    que el nuevo stock (no quedarian unidades disponibles).
  * Asignar a una orden: DISPO -1 / ENUSO +1 (rechaza si no hay DISPO).
  * Liberar de una orden (cerrar/cancelar/desasignar): ENUSO -1 / DISPO +1.
"""
from django.db import transaction
from rest_framework import serializers

from . import models

CODIGO_DISPO = "DISPO"
CODIGO_ENUSO = "ENUSO"


@transaction.atomic
def ajustar_stock_herramienta(herramienta, nuevo_stock):
    """Sincroniza HERRAMIENTA.stock con la M:M ESTADO_HERRAMIENTA.

    Al subir el stock, la cantidad aumentada entra como DISPO. Al bajar el
    stock se rechaza si los estados no disponibles suman mas que el nuevo
    stock; si pasa la validacion, el decremento se descuenta de DISPO."""
    estados = list(
        models.EstadoHerramienta.objects.filter(herramienta=herramienta)
        .select_related("edo_herramienta")
    )
    suma_no_dispo = sum(
        e.cantidad for e in estados if e.edo_herramienta.codigo != CODIGO_DISPO
    )
    if nuevo_stock < suma_no_dispo:
        raise serializers.ValidationError(
            f"No se puede bajar el stock a {nuevo_stock}: hay {suma_no_dispo} "
            "unidad(es) en estados no disponibles."
        )

    dispo = next(
        (e for e in estados if e.edo_herramienta.codigo == CODIGO_DISPO), None
    )
    cantidad_dispo = nuevo_stock - suma_no_dispo
    if dispo is not None:
        # OJO: ESTADO_HERRAMIENTA tiene PK compuesta (herramienta,
        # edo_herramienta) que Django emula como OneToOne; un save() con
        # update_fields solo usaria "herramienta" en el WHERE y pisaria los
        # demas estados. Se actualiza con .update() y la llave completa.
        models.EstadoHerramienta.objects.filter(
            herramienta=herramienta, edo_herramienta_id=CODIGO_DISPO
        ).update(cantidad=cantidad_dispo)
    elif cantidad_dispo > 0:
        models.EstadoHerramienta.objects.create(
            edo_herramienta=models.EdoHerramienta.objects.get(codigo=CODIGO_DISPO),
            herramienta=herramienta,
            cantidad=cantidad_dispo,
        )

    herramienta.stock = nuevo_stock
    herramienta.save(update_fields=["stock"])


def recalcular_stock_herramienta(herramienta):
    """Recalcula HERRAMIENTA.stock como la suma de las cantidades de la
    M:M ESTADO_HERRAMIENTA (equivalente a los triggers de REFACCION)."""
    total = sum(
        models.EstadoHerramienta.objects.filter(herramienta=herramienta)
        .values_list("cantidad", flat=True)
    )
    herramienta.stock = total
    herramienta.save(update_fields=["stock"])


def disponibles_herramienta(herramienta):
    """Cantidad de unidades DISPO (disponibles) de una herramienta."""
    row = herramientas_disponibles_map([herramienta]).get(herramienta.numeroregistro)
    return row or 0


def herramientas_disponibles_map(herramientas):
    """{numeroregistro: cantidad DISPO} para una lista de herramientas."""
    ids = [h.numeroregistro for h in herramientas]
    if not ids:
        return {}
    return dict(
        models.EstadoHerramienta.objects.filter(
            herramienta_id__in=ids,
            edo_herramienta_id=CODIGO_DISPO,
        ).values_list("herramienta_id", "cantidad")
    )


@transaction.atomic
def asignar_herramienta_a_orden(herramienta_id):
    """Reserva una unidad DISPO -> ENUSO para una orden de mantenimiento.

    Rechaza si la herramienta no tiene unidades disponibles."""
    herramienta = models.Herramienta.objects.get(pk=herramienta_id)
    dispo, _ = models.EstadoHerramienta.objects.get_or_create(
        herramienta=herramienta,
        edo_herramienta_id=CODIGO_DISPO,
        defaults={"cantidad": 0},
    )
    if dispo.cantidad <= 0:
        raise serializers.ValidationError(
            f"La herramienta '{herramienta.nombre}' no tiene unidades disponibles."
        )
    models.EstadoHerramienta.objects.filter(
        herramienta=herramienta, edo_herramienta_id=CODIGO_DISPO
    ).update(cantidad=dispo.cantidad - 1)

    enuso, _ = models.EstadoHerramienta.objects.get_or_create(
        herramienta=herramienta,
        edo_herramienta_id=CODIGO_ENUSO,
        defaults={"cantidad": 0},
    )
    models.EstadoHerramienta.objects.filter(
        herramienta=herramienta, edo_herramienta_id=CODIGO_ENUSO
    ).update(cantidad=enuso.cantidad + 1)


@transaction.atomic
def liberar_herramienta_de_orden(herramienta_id):
    """Devuelve una unidad ENUSO -> DISPO al cerrar/cancelar una orden o
    al quitar la herramienta de la misma."""
    herramienta = models.Herramienta.objects.get(pk=herramienta_id)
    enuso, _ = models.EstadoHerramienta.objects.get_or_create(
        herramienta=herramienta,
        edo_herramienta_id=CODIGO_ENUSO,
        defaults={"cantidad": 0},
    )
    if enuso.cantidad > 0:
        models.EstadoHerramienta.objects.filter(
            herramienta=herramienta, edo_herramienta_id=CODIGO_ENUSO
        ).update(cantidad=enuso.cantidad - 1)

    dispo, _ = models.EstadoHerramienta.objects.get_or_create(
        herramienta=herramienta,
        edo_herramienta_id=CODIGO_DISPO,
        defaults={"cantidad": 0},
    )
    models.EstadoHerramienta.objects.filter(
        herramienta=herramienta, edo_herramienta_id=CODIGO_DISPO
    ).update(cantidad=dispo.cantidad + 1)


@transaction.atomic
def validar_cantidad_estado_herramienta(herramienta, edo_codigo, nueva_cantidad):
    """Valida un cambio de cantidad en ESTADO_HERRAMIENTA antes de aplicarlo.

    DISPO (disponible) no puede quedar negativo: las unidades disponibles
    son el stock total menos lo que suman los estados no disponibles. La
    invariante HERRAMIENTA.stock = SUMA(cantidades) se aplica al guardar."""
    if nueva_cantidad < 0:
        raise serializers.ValidationError("La cantidad no puede ser negativa.")

    estados = list(
        models.EstadoHerramienta.objects.filter(herramienta=herramienta)
        .select_related("edo_herramienta")
    )
    suma_no_dispo = sum(
        e.cantidad for e in estados if e.edo_herramienta.codigo != CODIGO_DISPO
    )
    # El unico caso en que un cambio puede dejar a DISPO negativo es al
    # editar la propia fila DISPO (o borrarla, que es bajar a 0).
    if edo_codigo == CODIGO_DISPO:
        total_nuevo = suma_no_dispo + nueva_cantidad
        if total_nuevo < suma_no_dispo:
            raise serializers.ValidationError(
                "No se puede bajar el stock: las unidades en estados no "
                f"disponibles suman {suma_no_dispo}."
            )


def sync_estado_herramienta(herramienta, edo_codigo, nueva_cantidad):
    """Aplica un cambio de cantidad en ESTADO_HERRAMIENTA con la invariante
    de stock. Valida y recalcula HERRAMIENTA.stock."""
    with transaction.atomic():
        validar_cantidad_estado_herramienta(herramienta, edo_codigo, nueva_cantidad)
        row, _ = models.EstadoHerramienta.objects.get_or_create(
            herramienta=herramienta,
            edo_herramienta_id=edo_codigo,
            defaults={"cantidad": 0},
        )
        models.EstadoHerramienta.objects.filter(
            herramienta=herramienta, edo_herramienta_id=edo_codigo
        ).update(cantidad=nueva_cantidad)
        recalcular_stock_herramienta(herramienta)
