from django.utils import timezone
import os

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from apps.fallas.models import EstadoMaquina, Linea, Maquina, Marca, Modelo, TipoMaquina, TipoMaquinaArea

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

    def validate(self, datos):
        origen = datos.get("origen")
        maquina = datos.get("maquina")
        if origen == LecturaSensor.ORIGEN_IOT and maquina is not None:
            if maquina.modo_monitoreo != LecturaSensor.ORIGEN_IOT:
                raise serializers.ValidationError({"origen": "La máquina no está en modo IoT."})
        return datos


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
    estado_maquina = serializers.PrimaryKeyRelatedField(queryset=EstadoMaquina.objects.all(), required=False, allow_null=True)
    modo_monitoreo = serializers.ChoiceField(choices=LecturaSensor.ORIGENES, default=LecturaSensor.ORIGEN_SIMULADO)
    umbral_vibracion = serializers.FloatField(default=4.0, min_value=0)
    imagen = serializers.FileField(required=False, allow_null=True)
    modelo_3d_archivo = serializers.FileField(required=False, allow_null=True)

    def validate_codigo(self, valor):
        codigo = valor.strip().upper()
        if Maquina.objects.filter(codigo=codigo).exists():
            raise serializers.ValidationError("Ya existe una máquina con este código.")
        return codigo

    def validate(self, datos):
        linea = datos.get("linea")
        tipo_maquina = datos.get("tipo_maquina")
        if linea and tipo_maquina:
            restringido = TipoMaquinaArea.objects.filter(tipo_maquina=tipo_maquina).exists()
            if restringido and not TipoMaquinaArea.objects.filter(tipo_maquina=tipo_maquina, area=linea.area).exists():
                raise serializers.ValidationError({
                    "tipo_maquina": "Este tipo de máquina no es compatible con el área de esa línea."
                })
        return datos

    def create(self, datos):
        linea = datos.get("linea")
        marca = datos.get("marca")
        modelo = datos.get("modelo")
        tipo_maquina = datos.get("tipo_maquina")
        estado_maquina = datos.get("estado_maquina")

        imagen_url = None
        imagen_file = datos.get("imagen")
        if imagen_file:
            carpeta = os.path.join(settings.MEDIA_ROOT, "maquinaria")
            os.makedirs(carpeta, exist_ok=True)
            with open(os.path.join(carpeta, imagen_file.name), "wb+") as dest:
                for chunk in imagen_file.chunks():
                    dest.write(chunk)
            imagen_url = f"maquinaria/{imagen_file.name}"

        modelo_3d = None
        modelo_3d_file = datos.get("modelo_3d_archivo")
        if modelo_3d_file:
            carpeta = os.path.join(settings.MEDIA_ROOT, "maquinaria", "modelos3d")
            os.makedirs(carpeta, exist_ok=True)
            with open(os.path.join(carpeta, modelo_3d_file.name), "wb+") as dest:
                for chunk in modelo_3d_file.chunks():
                    dest.write(chunk)
            modelo_3d = f"maquinaria/modelos3d/{modelo_3d_file.name}"

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
            imagen_url=imagen_url,
            modelo_3d=modelo_3d,
        )


class ReporteFallaManualSerializer(serializers.Serializer):
    maquina = serializers.PrimaryKeyRelatedField(queryset=Maquina.objects.all())
    asunto = serializers.CharField(max_length=500)
    causaRaiz = serializers.CharField(max_length=500)
    descripcion = serializers.CharField(max_length=500, required=False, allow_blank=True)
    tiempoParo = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    tipo_falla = serializers.IntegerField()
    tipo_severidad = serializers.CharField(max_length=5)


class ModoMonitoreoSerializer(serializers.Serializer):
    """Cambia el modo de monitoreo de una máquina (manual/simulado/iot)."""
    modo_monitoreo = serializers.ChoiceField(choices=LecturaSensor.ORIGENES)

class ReparacionManualSerializer(serializers.Serializer):
    """Alimenta el MTTR a mano (para pruebas/expo). No expone mttr:
    lo calcula el trigger tg_actualizar_mttr_orden."""
    horas_reparacion = serializers.IntegerField(min_value=0)

class RegistroOpsSerializer(serializers.Serializer):
    """Registra un periodo de horas de operación de la máquina.
    No expone mtbf/mttr/disponibilidad: esos los calculan los triggers."""
    fechaInicio = serializers.DateField()
    fechaFin = serializers.DateField()
    horasOperacion = serializers.IntegerField(min_value=0)

    def validate(self, datos):
        if datos["fechaFin"] < datos["fechaInicio"]:
            raise serializers.ValidationError("fechaFin no puede ser anterior a fechaInicio.")
        return datos