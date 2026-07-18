from rest_framework import serializers
from . import models

#------------PLANTA-----------------------------------------------------
class ListPlantaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Planta
        fields = [
            "codigo",
            "nombre"
        ]

class DetailPlantaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Planta
        fields = "__all__"

class CreatePlantaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Planta
        fields = [
            "codigo",
            "nombre",
            "descripcion",
            "telefono",
            "dircalle",
            "dircodigopostal",
            "dirnumero"
        ]

class UpdatePlantaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Planta
        fields = [
            "codigo",
            "nombre",
            "descripcion",
            "telefono",
            "dircalle",
            "dircodigopostal",
            "dirnumero"
        ]

#------------AREA-----------------------------------------------------
class ListAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Area
        fields = [
            "codigo",
            "nombre",
            "planta"
        ]

class DetailAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Area
        fields = "__all__"

class CreateAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Area
        fields = [
            "codigo",
            "nombre",
            "descripcion",
            "telefono",
            "planta"
        ]

class UpdateAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Area
        fields = [
            "codigo",
            "nombre",
            "descripcion",
            "telefono",
            "planta"
        ]

#------------EDO MAQUINA----------------------------------------------------
class ListEdoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EdoMaquina
        fields = [
            "codigo",
            "nombre"
        ]

class DetailEdoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EdoMaquina
        fields = "__all__"

class CreateEdoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EdoMaquina
        fields = [
            "codigo",
            "nombre",
            "descripcion"
        ]

class UpdateEdoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EdoMaquina
        fields = [
            "codigo",
            "nombre",
            "descripcion"
        ]

#------------LINEA ----------------------------------------------------
class ListLineaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Linea
        fields = [
            "codigo",
            "nombre"
        ]
class DetailLineaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Linea
        fields = "__all__"

class CreateLineaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Linea
        fields = [
            "codigo",
            "nombre",
            "descripcion",
            "area"
        ]

class UpdateLineaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Linea
        fields = [
            "codigo",
            "nombre",
            "descripcion",
            "area"
        ]

#------------MARCA----------------------------------------------------
class ListMarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Marca
        fields = [
            "clave",
            "nombre"
        ]

class DetailMarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Marca
        fields = "__all__"

class CreateMarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Marca
        fields = [
            "clave",
            "nombre",
            "descripcion"
        ]

class UpdateMarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Marca
        fields = [
            "clave",
            "nombre",
            "descripcion"
        ]

#------------MODELO----------------------------------------------------
class ListModeloSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Modelo
        fields = [
            "codigo",
            "nombre",
            "marca"
        ]

class DetailModeloSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Modelo
        fields = "__all__"

class CreateModeloSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Modelo
        fields = [
            "codigo",
            "nombre",
            "descripcion",
            "marca"
        ]

class UpdateModeloSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Modelo
        fields = [
            "codigo",
            "nombre",
            "descripcion",
            "marca"
        ]

#------------TIPO MAQUINA----------------------------------------------------
class ListTipoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoMaquina
        fields = [
            "numeroregistro",
            "nombre"
        ]

class DetailTipoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoMaquina
        fields = "__all__"

class CreateTipoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoMaquina
        fields = [
            "nombre",
            "descripcion"
        ]

class UpdateTipoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoMaquina
        fields = [
            "nombre",
            "descripcion"
        ]

#------------MAQUINA----------------------------------------------------
class ListMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Maquina
        fields = [
            "codigo",
            "numeroserie",
            "nombre",
            "imagen_url",
            "marca",
            "modelo",
            "estado_maquina",
            "tipo_maquina"
        ]

class DetailMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Maquina
        fields = "__all__"

class CreateMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Maquina
        fields = [
            "codigo",
            "numeroserie",
            "nombre",
            "descripcion",
            "imagen_url",
            "fechainstalacion",
            "linea",
            "marca",
            "modelo",
            "estado_maquina",
            "tipo_maquina"
        ]

class UpdateMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Maquina
        fields = [
            "codigo",
            "numeroserie",
            "nombre",
            "descripcion",
            "imagen_url",
            "fechainstalacion",
            "linea",
            "marca",
            "modelo",
            "estado_maquina",
            "tipo_maquina"
        ]