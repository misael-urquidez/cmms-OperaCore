from rest_framework import serializers
from .models import (
    Planta,
    Area,
    EdoMaquina,
    Linea,
    Marca,
    Modelo,
    TipoMaquina,
    Maquina,
)
from apps.mantenimiento.models import Refaccion, OrdenMantenimiento
from apps.fallas.models import ReporteFalla
# ==========================================================
# PLANTA
# ==========================================================
class ListPlantaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Planta
        fields = ["codigo", "nombre"]

class DetailPlantaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Planta
        fields = "__all__"

class CreatePlantaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Planta
        fields = [
            "codigo", "nombre", "descripcion", "telefono",
            "dircalle", "dircodigopostal", "dirnumero"
        ]

class UpdatePlantaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Planta
        fields = [
            "codigo", "nombre", "descripcion", "telefono",
            "dircalle", "dircodigopostal", "dirnumero"
        ]


# ==========================================================
# AREA
# ==========================================================
class ListAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ["codigo", "nombre", "planta"]

class DetailAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = "__all__"

class CreateAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ["codigo", "nombre", "descripcion", "telefono", "planta"]

class UpdateAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ["codigo", "nombre", "descripcion", "telefono", "planta"]


# ==========================================================
# EDO MAQUINA
# ==========================================================
class ListEdoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EdoMaquina
        fields = ["codigo", "nombre"]

class DetailEdoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EdoMaquina
        fields = "__all__"

class CreateEdoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EdoMaquina
        fields = ["codigo", "nombre", "descripcion"]

class UpdateEdoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EdoMaquina
        fields = ["codigo", "nombre", "descripcion"]


# ==========================================================
# LINEA
# ==========================================================
class ListLineaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Linea
        fields = ["codigo", "nombre"]

class DetailLineaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Linea
        fields = "__all__"

class CreateLineaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Linea
        fields = ["codigo", "nombre", "descripcion", "area"]

class UpdateLineaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Linea
        fields = ["codigo", "nombre", "descripcion", "area"]


# ==========================================================
# MARCA
# ==========================================================
class ListMarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = ["clave", "nombre"]

class DetailMarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = "__all__"

class CreateMarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = ["clave", "nombre", "descripcion"]

class UpdateMarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = ["clave", "nombre", "descripcion"]


# ==========================================================
# MODELO
# ==========================================================
class ListModeloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modelo
        fields = ["codigo", "nombre", "marca"]

class DetailModeloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modelo
        fields = "__all__"

class CreateModeloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modelo
        fields = ["codigo", "nombre", "descripcion", "marca"]

class UpdateModeloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modelo
        fields = ["codigo", "nombre", "descripcion", "marca"]


# ==========================================================
# TIPO MAQUINA
# ==========================================================
class ListTipoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoMaquina
        fields = ["numeroregistro", "nombre"]

class DetailTipoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoMaquina
        fields = "__all__"

class CreateTipoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoMaquina
        fields = ["nombre", "descripcion"]

class UpdateTipoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoMaquina
        fields = ["nombre", "descripcion"]


# ==========================================================
# MAQUINA
# ==========================================================
class ListMaquinaSerializer(serializers.ModelSerializer):
    estado_maquina = serializers.StringRelatedField()
    tipo_maquina = serializers.StringRelatedField()
    linea = serializers.StringRelatedField()

    class Meta:
        model = Maquina
        fields = [
            "codigo", "numeroserie", "nombre", "imagen_url",
            "modelo_3d", "marca", "modelo","linea", "estado_maquina", "tipo_maquina"
        ]

class DetailMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Maquina
        fields = "__all__"

class CreateMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Maquina
        fields = [
            "codigo", "numeroserie", "nombre", "descripcion", "imagen_url",
            "modelo_3d", "fechainstalacion", "linea", "marca", "modelo",
            "estado_maquina", "tipo_maquina"
        ]

class UpdateMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Maquina
        fields = [
            "codigo", "numeroserie", "nombre", "descripcion", "imagen_url",
            "modelo_3d", "fechainstalacion", "linea", "marca", "modelo",
            "estado_maquina", "tipo_maquina"
        ]


# ==========================================================
# OTROS MÓDULOS (Piezas, Refacciones, Indicadores, Reportes, Órdenes)
# ==========================================================
#class PiezaSerializer(serializers.ModelSerializer):
#    class Meta:
#        model = Pieza
#        fields = "__all__"

class RefaccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refaccion
        fields = "__all__"

#class IndicadorSerializer(serializers.ModelSerializer):
#    class Meta:
#        model = Indicador
#        fields = "__all__"

class ReporteFallaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReporteFalla
        fields = "__all__"

class OrdenMantenimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdenMantenimiento
        fields = "__all__"