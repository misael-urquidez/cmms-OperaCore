from rest_framework import serializers
from . import models
from .models import *

# Aqui van tus serializers, igual que en las clases de tu maestro:
# uno por accion (list / detail / create / update). Ejemplo de patron
# a seguir en cuanto agregues campos a tus modelos:
#
# class ListMaquinaSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.Maquina
#         fields = ["id", "nombre", "status"]
#
# class DetailMaquinaSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.Maquina
#         fields = "__all__"
#
# class CreateMaquinaSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.Maquina
#         fields = ["nombre", "ubicacion"]

class PiezaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pieza
        fields = "__all__"  # Al ya no existir 'refaccion' en el modelo, Django mapeará automáticamente solo los campos reales.

class RefaccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refaccion
        fields = "__all__"


class IndicadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Indicador
        fields = "__all__"


class ReporteFallaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReporteFalla
        fields = "__all__"


class ListMaquinaSerializer(serializers.ModelSerializer):
    estado_maquina = serializers.StringRelatedField()
    tipo_maquina = serializers.StringRelatedField()

    class Meta:
        model = Maquina
        fields = (
            "codigo",
            "nombre",
            "linea",
            "estado_maquina",
            "marca",
            "modelo",
            "tipo_maquina",
            "imagen_url",
            "modelo_3d",
        )
        

class OrdenMantenimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdenMantenimiento
        fields = "__all__"


class DetailMaquinaSerializer(serializers.ModelSerializer):
    piezas = PiezaSerializer(many=True, read_only=True)
    indicadores = IndicadorSerializer(many=True, read_only=True)
    reportes_falla = ReporteFallaSerializer(many=True, read_only=True)
    ordenes_mantenimiento = OrdenMantenimientoSerializer(many=True, read_only=True)

    class Meta:
        model = Maquina
        fields = "__all__"