from rest_framework import serializers
from . import models

#------------TIPO FALLA ----------------------------------------------------
class ListTipoFallaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoFalla
        fields = [
            "numeroregistro",
            "nombre",
            "descripcion"
        ]

class DetailTipoFallaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoFalla
        fields = "__all__"

class CreateTipoFallaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoFalla
        fields = [
            "nombre",
            "descripcion"
        ]
    
class UpdateTipoFallaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoFalla
        fields = [
            "nombre",
            "descripcion"
        ]

#------------TIPO SEVERIDAD ----------------------------------------------------
class ListTipoSeveridadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoSeveridad
        fields = [
            "codigo",
            "nombre",
            "descripcion"
        ]

class DetailTipoSeveridadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoSeveridad
        fields = "__all__"

class CreateTipoSeveridadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoSeveridad
        fields = [
            "codigo",
            "nombre",
            "descripcion"
        ]

class UpdateTipoSeveridadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoSeveridad
        fields = [
            "codigo",
            "nombre",
            "descripcion"
        ]

#------------EDO REPORTE ----------------------------------------------------
class ListEdoReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EdoReporte
        fields = [
            "codigo",
            "nombre",
            "descripcion"
        ]

class DetailEdoReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EdoReporte
        fields = "__all__"

class CreateEdoReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EdoReporte
        fields = [
            "codigo",
            "nombre",
            "descripcion"
        ]

class UpdateEdoReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EdoReporte
        fields = [
            "codigo",
            "nombre",
            "descripcion"
        ]

#------------TIPO REPORTE ----------------------------------------------------
class ListTipoReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoReporte
        fields = [
            "tipo_falla",
            "reporte_falla"
        ]

class DetailTipoReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoReporte
        fields = "__all__"

class CreateTipoReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoReporte
        fields = [
            "tipo_falla",
            "reporte_falla"
        ]

class UpdateTipoReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoReporte
        fields = [
            "tipo_falla",
            "reporte_falla"
        ]

#------------REPORTE FALLA ----------------------------------------------------
class ListReporteFallaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ReporteFalla
        fields = [
            "numeroRegistro",
            "asunto",
            "fecharesolucion",
            "fechacreacion",
            "horacreacion",
            "tiempoparo",
            "causaraiz",
            "descripcion",
            "imagen",
            "maquina",
            "trabajador",
            "tipo_falla",
            "tipo_severidad"
        ]

class DetailReporteFallaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ReporteFalla
        fields = "__all__"

class CreateReporteFallaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ReporteFalla
        fields = [
            "asunto",
            "fecharesolucion",
            "fechacreacion",
            "horacreacion",
            "tiempoparo",
            "causaraiz",
            "descripcion",
            "imagen",
            "maquina",
            "trabajador",
            "tipo_falla",
            "tipo_severidad"
        ]

class UpdateReporteFallaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ReporteFalla
        fields = [
            "asunto",
            "fecharesolucion",
            "fechacreacion",
            "horacreacion",
            "tiempoparo",
            "causaraiz",
            "descripcion",
            "imagen",
            "maquina",
            "trabajador",
            "tipo_falla",
            "tipo_severidad"
        ]