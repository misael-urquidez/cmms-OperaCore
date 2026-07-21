from rest_framework import serializers

from .models import (
    Clasificacion,
    EdoHerramienta,
    EdoRefaccion,
    EstadoHerramienta,
    EstadoRefaccion,
    Herramienta,
    Movimiento,
    Proveedor,
    Refaccion,
    TipoHerramienta,
    TipoRefaccion,
)


# ---------------------------------------------------------------------
# Proveedor
# ---------------------------------------------------------------------

class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = [
            'codigo', 'rfc', 'razon_social', 'nombre_comercial',
            'telefono', 'email', 'dir_calle', 'dir_codigo_postal',
            'dir_numero', 'cont_nombre', 'cont_apell_pat', 'cont_apell_mat',
        ]


# ---------------------------------------------------------------------
# Refacción
# ---------------------------------------------------------------------

class EstadoRefaccionSerializer(serializers.ModelSerializer):
    estado_codigo = serializers.CharField(source='estado_refaccion.codigo', read_only=True)
    estado_nombre = serializers.CharField(source='estado_refaccion.nombre', read_only=True)

    class Meta:
        model = EstadoRefaccion
        fields = ['estado_codigo', 'estado_nombre', 'cantidad']


class RefaccionListSerializer(serializers.ModelSerializer):
    """Serializer ligero para la vista de listado (tabla con alerta de stock bajo)."""
    proveedor_nombre = serializers.CharField(
        source='proveedor.nombre_comercial', read_only=True, default=None,
    )
    stock_bajo = serializers.BooleanField(read_only=True)

    class Meta:
        model = Refaccion
        fields = [
            'numero_registro', 'nombre', 'codigo_sku', 'costo',
            'stock', 'stock_minimo', 'punto_reorden', 'tiempo_entrega_apr',
            'proveedor', 'proveedor_nombre', 'stock_bajo',
        ]


class RefaccionDetailSerializer(serializers.ModelSerializer):
    """Serializer completo, incluye proveedor expandido y desglose por estado."""
    proveedor = ProveedorSerializer(read_only=True)
    estados = EstadoRefaccionSerializer(many=True, read_only=True)
    stock_bajo = serializers.BooleanField(read_only=True)

    class Meta:
        model = Refaccion
        fields = [
            'numero_registro', 'nombre', 'codigo_sku', 'codigo_inventario',
            'numero_orden', 'costo', 'tiempo_entrega_apr', 'stock',
            'stock_minimo', 'punto_reorden', 'proveedor', 'tipo_refaccion',
            'clasificacion', 'stock_bajo', 'estados',
        ]


# ---------------------------------------------------------------------
# Herramienta
# ---------------------------------------------------------------------

class EstadoHerramientaSerializer(serializers.ModelSerializer):
    edo_codigo = serializers.CharField(source='edo_herramienta.codigo', read_only=True)
    edo_nombre = serializers.CharField(source='edo_herramienta.nombre', read_only=True)

    class Meta:
        model = EstadoHerramienta
        fields = ['edo_codigo', 'edo_nombre', 'cantidad']


class HerramientaListSerializer(serializers.ModelSerializer):
    tipo_nombre = serializers.CharField(
        source='tipo_herramienta.nombre', read_only=True, default=None,
    )

    class Meta:
        model = Herramienta
        fields = ['numero_registro', 'nombre', 'descripcion', 'imagen', 'tipo_herramienta', 'tipo_nombre']


class HerramientaDetailSerializer(serializers.ModelSerializer):
    estados = EstadoHerramientaSerializer(many=True, read_only=True)

    class Meta:
        model = Herramienta
        fields = ['numero_registro', 'nombre', 'descripcion', 'imagen', 'tipo_herramienta', 'estados']


# ---------------------------------------------------------------------
# Movimiento (entradas / salidas)
# ---------------------------------------------------------------------

class MovimientoCreateSerializer(serializers.ModelSerializer):
    """
    Registra un movimiento y ajusta el stock de la refacción.

    OJO: la tabla MOVIMIENTO en beta.sql NO tiene columna "cantidad"
    (se quitó a propósito según el comentario del .sql). Por eso aquí
    "cantidad" es un campo write-only que NO se guarda en Movimiento:
    solo se usa para saber cuánto sumar o restar al stock de la
    refacción. Si el equipo decide regresar la columna a la tabla,
    hay que agregarla también a models.Movimiento y quitar esta nota.
    """
    cantidad = serializers.IntegerField(write_only=True, min_value=1)

    class Meta:
        model = Movimiento
        fields = [
            'numero_registro', 'descripcion', 'fecha', 'hora',
            'tipo_movimiento', 'orden_mantenimiento', 'refaccion', 'cantidad',
        ]
        read_only_fields = ['numero_registro']

    def validate(self, data):
        tipo = data.get('tipo_movimiento')
        refaccion = data.get('refaccion')
        cantidad = data.get('cantidad')

        if tipo == Movimiento.SALIDA and refaccion is not None and cantidad is not None:
            if refaccion.stock < cantidad:
                raise serializers.ValidationError(
                    f'Stock insuficiente para "{refaccion.nombre}": hay '
                    f'{refaccion.stock} unidades y se intentan sacar {cantidad}.'
                )
        return data

    def create(self, validated_data):
        cantidad = validated_data.pop('cantidad')
        movimiento = Movimiento.objects.create(**validated_data)

        refaccion = movimiento.refaccion
        if refaccion is not None:
            if movimiento.tipo_movimiento == Movimiento.ENTRADA:
                refaccion.stock += cantidad
            else:
                refaccion.stock = max(refaccion.stock - cantidad, 0)
            refaccion.save(update_fields=['stock'])

        return movimiento
