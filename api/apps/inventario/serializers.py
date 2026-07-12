from rest_framework import serializers
from . import models

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
