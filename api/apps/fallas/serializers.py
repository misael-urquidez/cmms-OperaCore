from datetime import date, datetime
import os

from django.conf import settings
from rest_framework import serializers

from . import models


class TipoSeveridadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoSeveridad
        fields = ["codigo", "nombre"]


class TipoFallaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoFalla
        fields = ["numeroRegistro", "nombre"]


class MaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Maquina
        fields = ["codigo", "nombre"]


class EstadoReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EstadoReporte
        fields = ["codigo", "nombre"]


class ReporteFallaListSerializer(serializers.ModelSerializer):


    maquina_nombre = serializers.CharField(source="maquina.nombre", read_only=True, default=None)
    trabajador_nombre = serializers.SerializerMethodField()
    tipo_falla_nombre = serializers.CharField(
        source="tipo_falla.nombre", read_only=True, default=None
    )
    tipo_severidad_nombre = serializers.CharField(
        source="tipo_severidad.nombre", read_only=True, default=None
    )

    class Meta:
        model = models.ReporteFalla
        fields = [
            "numeroRegistro", "asunto", "fechaCreacion", "horaCreacion",
            "tiempoParo", "causaRaiz", "descripcion",
            "maquina", "maquina_nombre",
            "trabajador", "trabajador_nombre",
            "tipo_falla", "tipo_falla_nombre",
            "tipo_severidad", "tipo_severidad_nombre",
        ]

    def get_trabajador_nombre(self, obj):
        if obj.trabajador:
            return f"{obj.trabajador.nombre} {obj.trabajador.apellidoPat}"
        return None


class ReporteFallaDetailSerializer(serializers.ModelSerializer):


    maquina_nombre = serializers.CharField(source="maquina.nombre", read_only=True, default=None)
    trabajador_nombre = serializers.SerializerMethodField()
    tipo_falla_nombre = serializers.CharField(
        source="tipo_falla.nombre", read_only=True, default=None
    )
    tipo_severidad_nombre = serializers.CharField(
        source="tipo_severidad.nombre", read_only=True, default=None
    )

    class Meta:
        model = models.ReporteFalla
        fields = "__all__"

    def get_trabajador_nombre(self, obj):
        if obj.trabajador:
            return f"{obj.trabajador.nombre} {obj.trabajador.apellidoPat}"
        return None


class ReporteFallaCreateSerializer(serializers.ModelSerializer):
    imagen = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = models.ReporteFalla
        fields = [
            "asunto", "descripcion", "causaRaiz", "tiempoParo",
            "maquina", "tipo_falla", "tipo_severidad", "imagen", "estado_reporte",
        ]

    def create(self, validated_data):
        imagen_file = validated_data.pop("imagen", None)

        validated_data["fechaCreacion"] = date.today()
        validated_data["horaCreacion"] = datetime.now().time()
        validated_data["fechaResolucion"] = date.today()
        trabajador = self.context["request"].session.get("usuario")
        if trabajador:
            validated_data["trabajador"] = trabajador["numeroNomina"]

        reporte = super().create(validated_data)

        if imagen_file:
            carpeta = os.path.join(settings.MEDIA_ROOT, "fallas")
            os.makedirs(carpeta, exist_ok=True)
            ruta = os.path.join(carpeta, imagen_file.name)
            with open(ruta, "wb+") as dest:
                for chunk in imagen_file.chunks():
                    dest.write(chunk)
            reporte.imagen = f"fallas/{imagen_file.name}"
            reporte.save(update_fields=["imagen"])

        return reporte
