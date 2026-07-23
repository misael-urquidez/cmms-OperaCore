from datetime import date, datetime
import os

from django.conf import settings
from rest_framework import serializers

from .models import (
    TipoSeveridad,
    TipoFalla,
    EstadoReporte,
    ReporteFalla,
    TipoReporte,
)
from apps.usuarios.models import Trabajador
from apps.maquinaria.models import Maquina

#---------------- TIPO SEVERIDAD --------------------------------
class TipoSeveridadSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoSeveridad
        fields = ["codigo", "nombre"]


class TipoSeveridadCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoSeveridad
        fields = ["codigo", "nombre", "descripcion"]


class TipoSeveridadDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoSeveridad
        fields = "__all__"


#---------------- TIPO FALLA --------------------------------
class TipoFallaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoFalla
        fields = ["numeroRegistro", "nombre"]


class TipoFallaCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoFalla
        fields = ["nombre", "descripcion"]


class TipoFallaDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoFalla
        fields = "__all__"


#---------------- ESTADO REPORTE--------------------------------
class EstadoReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadoReporte
        fields = ["codigo", "nombre"]

class EstadoReporteDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadoReporte
        fields = "__all__"


#---------------- REPORTE FALLA --------------------------------
class ReporteFallaListSerializer(serializers.ModelSerializer):
    maquina_nombre = serializers.CharField(source="maquina.nombre", read_only=True, default=None)
    trabajador_nombre = serializers.SerializerMethodField()
    tipo_severidad_nombre = serializers.CharField(
        source="tipo_severidad.nombre", read_only=True, default=None
    )

    class Meta:
        model = ReporteFalla
        fields = [
            "numeroRegistro", "asunto", "fechaCreacion", "horaCreacion",
            "tiempoParo", "causaRaiz", "descripcion",
            "maquina", "maquina_nombre",
            "trabajador", "trabajador_nombre",
            "tipo_severidad", "tipo_severidad_nombre",
        ]

    def get_trabajador_nombre(self, obj):
        if obj.trabajador:
            return f"{obj.trabajador.nombre} {obj.trabajador.apellidoPat}"
        return None


class ReporteFallaDetailSerializer(serializers.ModelSerializer):
    maquina_nombre = serializers.CharField(source="maquina.nombre", read_only=True, default=None)
    trabajador_nombre = serializers.SerializerMethodField()
    estado_reporte_nombre = serializers.CharField(
        source="estado_reporte.nombre", read_only=True, default=None
    )
    tipo_severidad_nombre = serializers.CharField(
        source="tipo_severidad.nombre", read_only=True, default=None
    )
    fallas_asociadas = serializers.SerializerMethodField()

    class Meta:
        model = ReporteFalla
        fields = "__all__"

    def get_trabajador_nombre(self, obj):
        if obj.trabajador:
            return f"{obj.trabajador.nombre} {obj.trabajador.apellidoPat}"
        return None

    def get_fallas_asociadas(self, obj):
        registros = (
            TipoReporte.objects
            .filter(reporte_falla=obj)
            .values_list("tipo_falla_id", flat=True)
        )
        fallas = []
        for tf_id in registros:
            try:
                tf = TipoFalla.objects.get(pk=tf_id)
                fallas.append({"id": tf.numeroRegistro, "nombre": tf.nombre})
            except TipoFalla.DoesNotExist:
                continue
        return fallas


class ReporteFallaCreateSerializer(serializers.ModelSerializer):
    imagen = serializers.FileField(required=False, allow_null=True)
    tipo_falla_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True
    )
    class Meta:
        model = ReporteFalla
        fields = [
            "asunto", "descripcion", "causaRaiz", "tiempoParo", "fechaResolucion",
            "maquina", "trabajador", "tipo_severidad", "imagen",
            "estado_reporte", "tipo_falla_ids",
        ]

    def create(self, validated_data):
        imagen_file = validated_data.pop("imagen", None)
        tipo_falla_ids = validated_data.pop("tipo_falla_ids", [])

        validated_data["fechaCreacion"] = date.today()
        validated_data["horaCreacion"] = datetime.now().time()

        if not validated_data.get("fechaResolucion"):
            validated_data["fechaResolucion"] = date.today()

        if not validated_data.get("trabajador"):
            trabajador = self.context["request"].session.get("usuario")
            if trabajador:
                validated_data["trabajador"] = trabajador["numeroNomina"]

        reporte = super().create(validated_data)

        for tf_id in tipo_falla_ids:
            TipoReporte.objects.create(
                tipo_falla_id=tf_id,
                reporte_falla=reporte,
            )

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


class ReporteFallaUpdateSerializer(serializers.ModelSerializer):
    imagen = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = ReporteFalla
        fields = [
            "asunto", "descripcion", "causaRaiz", "tiempoParo", "fechaResolucion",
            "maquina", "trabajador", "tipo_severidad", "imagen", "estado_reporte",
        ]


# ------------ TIPO_REPORTE (llave compuesta: tipo_falla, reporte_falla) --
class ListTipoReporteSerializer(serializers.ModelSerializer):
    tipo_falla_nombre = serializers.CharField(
        source="tipo_falla.nombre", read_only=True, default=None
    )

    class Meta:
        model = TipoReporte
        fields = ["tipo_falla", "reporte_falla", "tipo_falla_nombre"]
        # No tiene id — pk compuesta


class DetailTipoReporteSerializer(serializers.ModelSerializer):
    tipo_falla_nombre = serializers.CharField(
        source="tipo_falla.nombre", read_only=True, default=None
    )

    class Meta:
        model = TipoReporte
        fields = ["tipo_falla", "reporte_falla", "tipo_falla_nombre"]
        # No tiene id — pk compuesta


class CreateTipoReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoReporte
        fields = ["tipo_falla", "reporte_falla"]
        # No tiene id — pk compuesta


#---------------- EXTRAS --------------------------------
class MaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Maquina
        fields = ["codigo", "nombre"]


class TrabajadorLightSerializer(serializers.ModelSerializer):
    """Serializer ligero para el select de trabajadores en el reporte de falla."""

    class Meta:
        model = Trabajador
        fields = ["numeroNomina", "nombre", "apellidoPat"]