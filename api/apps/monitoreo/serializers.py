from django.utils import timezone
from rest_framework import serializers

from apps.maquinaria.models import (
    EdoMaquina, Linea, Maquina, Marca, Modelo, TipoMaquina, 
)
from . import services
from .models import LecturaSensor


class LecturaSensorSerializer(serializers.ModelSerializer):
    maquina = serializers.PrimaryKeyRelatedField(queryset=Maquina.objects.all())

    class Meta:
        model = LecturaSensor
        fields = ["numeroRegistro", "maquina", "timestamp", "origen", "vibracion", "golpe", "temperatura"]
        read_only_fields = ["numeroRegistro", "timestamp"]

    def create(self, validated_data):
        lectura, reporte, requiere_revision = services.registrar_lectura(**validated_data)
        self.context["reporte_automatico"] = reporte
        self.context["requiere_revision"] = requiere_revision
        return lectura

    def validate_origen(self, origen):
        if origen == LecturaSensor.ORIGEN_IOT:
            raise serializers.ValidationError("El origen IoT se habilitará en una fase posterior.")
        return origen


class CrearMaquinaSerializer(serializers.Serializer):
    """Alta de máquina desde el mapa de planta. No usa ModelSerializer porque
    Maquina.marca/modelo/estado_maquina/tipo_maquina son columnas planas
    (no ForeignKey a nivel de modelo), así que el mapeo a instancias de
    catálogo se hace aquí y se guardan solo sus códigos."""

    codigo = serializers.CharField(max_length=10)
    nombre = serializers.CharField(max_length=100)
    descripcion = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    numeroSerie = serializers.CharField(max_length=30, required=False, allow_blank=True, allow_null=True)
    fechaInstalacion = serializers.DateField(required=False)
    linea = serializers.PrimaryKeyRelatedField(queryset=Linea.objects.all(), required=False, allow_null=True)
    marca = serializers.PrimaryKeyRelatedField(queryset=Marca.objects.all(), required=False, allow_null=True)
    modelo = serializers.PrimaryKeyRelatedField(queryset=Modelo.objects.all(), required=False, allow_null=True)
    tipo_maquina = serializers.PrimaryKeyRelatedField(queryset=TipoMaquina.objects.all(), required=False, allow_null=True)
    estado_maquina = serializers.PrimaryKeyRelatedField(queryset=EdoMaquina.objects.all(), required=False, allow_null=True)
    modo_monitoreo = serializers.ChoiceField(choices=LecturaSensor.ORIGENES, default=LecturaSensor.ORIGEN_SIMULADO)
    umbral_vibracion = serializers.FloatField(default=4.0, min_value=0)

    def validate_codigo(self, valor):
        codigo = valor.strip().upper()
        if Maquina.objects.filter(codigo=codigo).exists():
            raise serializers.ValidationError("Ya existe una máquina con este código.")
        return codigo

    def create(self, datos):
        linea = datos.get("linea")
        marca = datos.get("marca")
        modelo = datos.get("modelo")
        tipo_maquina = datos.get("tipo_maquina")
        estado_maquina = datos.get("estado_maquina")
        return Maquina.objects.create(
            codigo=datos["codigo"],
            nombre=datos["nombre"],
            descripcion=datos.get("descripcion") or None,
            numeroSerie=datos.get("numeroSerie") or None,
            fechaInstalacion=datos.get("fechaInstalacion") or timezone.localdate(),
            linea=linea,
            marca=marca.clave if marca else None,
            modelo=modelo.codigo if modelo else None,
            tipo_maquina=tipo_maquina.numeroRegistro if tipo_maquina else None,
            estado_maquina=estado_maquina.codigo if estado_maquina else "OPERA",
            modo_monitoreo=datos["modo_monitoreo"],
            umbral_vibracion=datos["umbral_vibracion"],
        )


class ReporteFallaManualSerializer(serializers.Serializer):
    maquina = serializers.PrimaryKeyRelatedField(queryset=Maquina.objects.all())
    asunto = serializers.CharField(max_length=500)
    causaRaiz = serializers.CharField(max_length=500)
    descripcion = serializers.CharField(max_length=500, required=False, allow_blank=True)
    tiempoParo = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    tipo_falla = serializers.IntegerField()
    tipo_severidad = serializers.CharField(max_length=5)