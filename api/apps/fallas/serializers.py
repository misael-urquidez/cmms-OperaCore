from datetime import date, datetime

from rest_framework import serializers

from . import models


class TipoSeveridadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoSeveridad
        fields = ["codigo", "nombre"]


class TipoSeveridadCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoSeveridad
        fields = ["codigo", "nombre", "descripcion"]


class TipoFallaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoFalla
        fields = ["numeroRegistro", "nombre"]


class TipoFallaCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoFalla
        fields = ["nombre", "descripcion"]


class TipoSeveridadDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoSeveridad
        fields = "__all__"


class TipoFallaDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoFalla
        fields = "__all__"


class EstadoReporteDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EstadoReporte
        fields = "__all__"


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

    class Meta:
        model = models.ReporteFalla
        fields = [
            "asunto", "descripcion", "causaRaiz", "tiempoParo",
            "maquina", "tipo_falla", "tipo_severidad",
        ]

    def create(self, validated_data):
        validated_data["fechaCreacion"] = date.today()
        validated_data["horaCreacion"] = datetime.now().time()
        validated_data["estado_reporte"] = models.EstadoReporte.objects.get(codigo="ABIER")
        trabajador = self.context["request"].session.get("usuario")
        if trabajador:
            validated_data["trabajador_id"] = trabajador["numeroNomina"]
        return super().create(validated_data)


# ------------ TIPO_REPORTE (llave compuesta: tipo_falla, reporte_falla) --
class ListTipoReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoReporte
        fields = ["tipo_falla", "reporte_falla"]


class DetailTipoReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoReporte
        fields = "__all__"


class CreateTipoReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoReporte
        fields = ["tipo_falla", "reporte_falla"]


class UpdateTipoReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoReporte
        fields = ["tipo_falla", "reporte_falla"]
