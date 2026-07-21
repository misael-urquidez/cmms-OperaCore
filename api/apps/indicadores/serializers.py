from rest_framework import serializers
from . import models

# ------------ INDICADOR --------------------------------------------------------
class ListIndicadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Indicador
        fields = ["numeroregistro", "fechainicio", "fechafin", "maquina"]

class DetailIndicadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Indicador
        fields = "__all__"

class CreateIndicadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Indicador
        fields = [
            "fechainicio",
            "fechafin",
            "mttr",
            "mtbf",
            "porcentajedispo",
            "maquina",
        ]

class UpdateIndicadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Indicador
        fields = [
            "fechainicio",
            "fechafin",
            "mttr",
            "mtbf",
            "porcentajedispo",
            "maquina",
        ]
