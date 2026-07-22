from rest_framework import serializers
from . import models

# ------------ CLASIFICACION ----------------------------------------------------
class ListClasificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Clasificacion
        fields = ["codigo", "nombre"]

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
        fields = ["codigo", "nombre"]

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
        fields = ["codigo", "nombre"]

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
        fields = ["codigo", "nombre"]

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
        fields = ["numeroregistro", "nombre"]

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
        fields = ["numeroregistro", "nombre"]

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
        fields = ["numeroregistro", "nombre"]

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
        fields = ["codigo", "rfc", "razonsocial", "nombrecomercial", "telefono"]

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
        fields = ["numeroregistro", "nombre", "tipo_herramienta"]

class DetailHerramientaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Herramienta
        fields = "__all__"

class CreateHerramientaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Herramienta
        fields = ["nombre", "descripcion", "imagen", "tipo_herramienta"]

class UpdateHerramientaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Herramienta
        fields = ["nombre", "descripcion", "imagen", "tipo_herramienta"]


# ------------ PIEZA ------------------------------------------------------------
class ListPiezaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Pieza
        fields = ["numeroserie", "codigoetiqueta", "nombre", "maquina", "edo_pieza"]

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
        fields = ["numeroregistro", "nombre", "codigosku", "stock", "proveedor"]

class DetailRefaccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Refaccion
        fields = "__all__"

class CreateRefaccionSerializer(serializers.ModelSerializer):
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

class UpdateRefaccionSerializer(serializers.ModelSerializer):
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


# ------------ TABLAS DE RELACION / INTERMEDIAS ---------------------------------
class ListRefaccMaquiSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RefaccMaqui
        fields = ["maquina", "refaccion"]

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
        fields = ["herramienta", "edo_herramienta", "cantidad"]

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
        fields = ["estado_refaccion", "refaccion", "cantidad"]

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
