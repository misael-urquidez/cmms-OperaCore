from rest_framework import serializers
import os
from django.conf import settings
from django.db import transaction
from . import models

CODIGO_DISPO = "DISPO"

# ------------ CLASIFICACION ----------------------------------------------------
class ListClasificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Clasificacion
        fields = "__all__"

class DetailClasificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Clasificacion
        fields = "__all__"

class CreateClasificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Clasificacion
        fields = ["codigo", "nombre", "descripcion"]

class UpdateClasificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Clasificacion
        fields = ["codigo", "nombre", "descripcion"]


# ------------ EDO HERRAMIENTA --------------------------------------------------
class ListEdoHerramientaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EdoHerramienta
        fields = "__all__"

class DetailEdoHerramientaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EdoHerramienta
        fields = "__all__"

class CreateEdoHerramientaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EdoHerramienta
        fields = ["codigo", "nombre", "descripcion"]

class UpdateEdoHerramientaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EdoHerramienta
        fields = ["codigo", "nombre", "descripcion"]


# ------------ EDO PIEZA --------------------------------------------------------
class ListEdoPiezaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EdoPieza
        fields = "__all__"

class DetailEdoPiezaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EdoPieza
        fields = "__all__"

class CreateEdoPiezaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EdoPieza
        fields = ["codigo", "nombre", "descripcion"]

class UpdateEdoPiezaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EdoPieza
        fields = ["codigo", "nombre", "descripcion"]


# ------------ EDO REFACCION ----------------------------------------------------
class ListEdoRefaccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EdoRefaccion
        fields = "__all__"

class DetailEdoRefaccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EdoRefaccion
        fields = "__all__"

class CreateEdoRefaccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EdoRefaccion
        fields = ["codigo", "nombre", "descripcion"]

class UpdateEdoRefaccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EdoRefaccion
        fields = ["codigo", "nombre", "descripcion"]


# ------------ TIPO HERRAMIENTA --------------------------------------------------
class ListTipoHerramientaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoHerramienta
        fields = "__all__"

class DetailTipoHerramientaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoHerramienta
        fields = "__all__"

class CreateTipoHerramientaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoHerramienta
        fields = ["nombre", "descripcion"]

class UpdateTipoHerramientaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoHerramienta
        fields = ["nombre", "descripcion"]


# ------------ TIPO PIEZA --------------------------------------------------------
class ListTipoPiezaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoPieza
        fields = "__all__"

class DetailTipoPiezaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoPieza
        fields = "__all__"

class CreateTipoPiezaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoPieza
        fields = ["nombre", "descripcion"]

class UpdateTipoPiezaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoPieza
        fields = ["nombre", "descripcion"]


# ------------ TIPO REFACCION ----------------------------------------------------
class ListTipoRefaccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoRefaccion
        fields = "__all__"

class DetailTipoRefaccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoRefaccion
        fields = "__all__"

class CreateTipoRefaccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoRefaccion
        fields = ["nombre", "descripcion"]

class UpdateTipoRefaccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoRefaccion
        fields = ["nombre", "descripcion"]


# ------------ PROVEEDOR --------------------------------------------------------
class ListProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Proveedor
        fields = "__all__"

class DetailProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Proveedor
        fields = "__all__"

class CreateProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Proveedor
        fields = [
            "codigo",
            "rfc",
            "razonsocial",
            "nombrecomercial",
            "telefono",
            "email",
            "dircalle",
            "dircodigopostal",
            "dirnumero",
            "contnombre",
            "contapellpat",
            "contapellmat",
        ]

class UpdateProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Proveedor
        fields = [
            "codigo",
            "rfc",
            "razonsocial",
            "nombrecomercial",
            "telefono",
            "email",
            "dircalle",
            "dircodigopostal",
            "dirnumero",
            "contnombre",
            "contapellpat",
            "contapellmat",
        ]


# ------------ HERRAMIENTA -------------------------------------------------------
class ListHerramientaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Herramienta
        fields = "__all__"

class DetailHerramientaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Herramienta
        fields = "__all__"

class CreateHerramientaSerializer(serializers.ModelSerializer):
    imagen = serializers.FileField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = models.Herramienta
        fields = ["nombre", "descripcion", "imagen", "tipo_herramienta"]

    def create(self, validated_data):
        imagen_file = validated_data.pop("imagen", None)
        if imagen_file:
            carpeta = os.path.join(settings.MEDIA_ROOT, "inventario")
            os.makedirs(carpeta, exist_ok=True)
            ruta = os.path.join(carpeta, imagen_file.name)
            with open(ruta, "wb+") as dest:
                for chunk in imagen_file.chunks():
                    dest.write(chunk)
            validated_data["imagen"] = f"inventario/{imagen_file.name}"
        return super().create(validated_data)

class UpdateHerramientaSerializer(serializers.ModelSerializer):
    imagen = serializers.FileField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = models.Herramienta
        fields = ["nombre", "descripcion", "imagen", "tipo_herramienta"]

    def update(self, instance, validated_data):
        imagen_file = validated_data.pop("imagen", None)
        if imagen_file:
            carpeta = os.path.join(settings.MEDIA_ROOT, "inventario")
            os.makedirs(carpeta, exist_ok=True)
            ruta = os.path.join(carpeta, imagen_file.name)
            with open(ruta, "wb+") as dest:
                for chunk in imagen_file.chunks():
                    dest.write(chunk)
            validated_data["imagen"] = f"inventario/{imagen_file.name}"
        return super().update(instance, validated_data)


# ------------ PIEZA ------------------------------------------------------------
class ListPiezaSerializer(serializers.ModelSerializer):
    porcentaje_desgaste = serializers.FloatField(read_only=True)

    class Meta:
        model = models.Pieza
        fields = "__all__"

class DetailPiezaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Pieza
        fields = "__all__"

class CreatePiezaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Pieza
        fields = [
            "numeroserie",
            "codigoetiqueta",
            "nombre",
            "costoinicial",
            "horasoperacion",
            "tiempovidautil",
            "depresacionanual",
            "valorresidual",
            "fechainstalacion",
            "fechagarantia",
            "edo_pieza",
            "maquina",
            "tipo_pieza",
        ]

class UpdatePiezaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Pieza
        fields = [
            "numeroserie",
            "codigoetiqueta",
            "nombre",
            "costoinicial",
            "horasoperacion",
            "tiempovidautil",
            "depresacionanual",
            "valorresidual",
            "fechainstalacion",
            "fechagarantia",
            "edo_pieza",
            "maquina",
            "tipo_pieza",
        ]


# ------------ REFACCION --------------------------------------------------------
class ListRefaccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Refaccion
        fields = "__all__"

class DetailRefaccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Refaccion
        fields = "__all__"

@transaction.atomic
def _ajustar_stock_refaccion(refaccion, nuevo_stock):
    """Mantiene la M:M ESTADO_REFACCION consistente con REFACCION.stock.

    Al subir el stock, la cantidad aumentada entra como DISPO (disponible).
    Al bajar el stock se rechaza si los estados no disponibles suman mas que
    el nuevo stock (no quedarian unidades disponibles); si pasa la
    validacion, el decremento se descuenta de DISPO."""
    estados = list(refaccion.estadorefaccion_set.select_related("estado_refaccion"))
    suma_no_dispo = sum(
        e.cantidad for e in estados if e.estado_refaccion.codigo != CODIGO_DISPO
    )
    if nuevo_stock < suma_no_dispo:
        raise serializers.ValidationError(
            f"No se puede bajar el stock a {nuevo_stock}: hay {suma_no_dispo} "
            "unidad(es) en estados no disponibles."
        )

    dispo = next(
        (e for e in estados if e.estado_refaccion.codigo == CODIGO_DISPO), None
    )
    cantidad_dispo = nuevo_stock - suma_no_dispo
    if dispo is not None:
        dispo.cantidad = cantidad_dispo
        dispo.save(update_fields=["cantidad"])
    elif cantidad_dispo > 0:
        models.EstadoRefaccion.objects.create(
            estado_refaccion=models.EdoRefaccion.objects.get(codigo=CODIGO_DISPO),
            refaccion=refaccion,
            cantidad=cantidad_dispo,
        )

    refaccion.stock = nuevo_stock
    refaccion.save(update_fields=["stock"])


class CreateRefaccionSerializer(serializers.ModelSerializer):
    codigoinventario = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    numeroorden = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = models.Refaccion
        fields = [
            "nombre",
            "codigosku",
            "puntoreorden",
            "codigoinventario",
            "numeroorden",
            "costo",
            "tiempoentregaapr",
            "stock",
            "stockminimo",
            "proveedor",
            "tipo_refaccion",
            "clasificacion",
        ]

    def create(self, validated_data):
        with transaction.atomic():
            refaccion = super().create(validated_data)
            stock = validated_data.get("stock")
            if stock and stock > 0:
                _ajustar_stock_refaccion(refaccion, stock)
        return refaccion

class UpdateRefaccionSerializer(serializers.ModelSerializer):
    codigoinventario = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    numeroorden = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = models.Refaccion
        fields = [
            "nombre",
            "codigosku",
            "puntoreorden",
            "codigoinventario",
            "numeroorden",
            "costo",
            "tiempoentregaapr",
            "stock",
            "stockminimo",
            "proveedor",
            "tipo_refaccion",
            "clasificacion",
        ]

    def update(self, instance, validated_data):
        with transaction.atomic():
            if "stock" in validated_data:
                _ajustar_stock_refaccion(instance, validated_data["stock"])
            refaccion = super().update(instance, validated_data)
        return refaccion


# ------------ TABLAS DE RELACION / INTERMEDIAS ---------------------------------
class ListRefaccMaquiSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RefaccMaqui
        fields = "__all__"

class DetailRefaccMaquiSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RefaccMaqui
        fields = "__all__"

class CreateRefaccMaquiSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RefaccMaqui
        fields = ["maquina", "refaccion"]

class UpdateRefaccMaquiSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RefaccMaqui
        fields = ["maquina", "refaccion"]


class ListEstadoHerramientaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EstadoHerramienta
        fields = "__all__"

class DetailEstadoHerramientaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EstadoHerramienta
        fields = "__all__"

class CreateEstadoHerramientaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EstadoHerramienta
        fields = ["herramienta", "edo_herramienta", "cantidad"]

class UpdateEstadoHerramientaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EstadoHerramienta
        fields = ["herramienta", "edo_herramienta", "cantidad"]


class ListEstadoRefaccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EstadoRefaccion
        fields = "__all__"

class DetailEstadoRefaccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EstadoRefaccion
        fields = "__all__"

class CreateEstadoRefaccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EstadoRefaccion
        fields = ["estado_refaccion", "refaccion", "cantidad"]

class UpdateEstadoRefaccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EstadoRefaccion
        fields = ["estado_refaccion", "refaccion", "cantidad"]
