from rest_framework import serializers
import os
from django.conf import settings
from .models import (
    Planta,
    Area,
    EdoMaquina,
    Linea,
    Marca,
    Modelo,
    TipoMaquina,
    TipoMaquinaArea,
    Maquina,
)
from apps.mantenimiento.models import Refaccion, OrdenMantenimiento
from apps.fallas.models import ReporteFalla
# ==========================================================
# PLANTA
# ==========================================================
class ListPlantaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Planta
        fields = "__all__"

class DetailPlantaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Planta
        fields = "__all__"

class CreatePlantaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Planta
        fields = [
            "codigo", "nombre", "descripcion", "telefono",
            "dircalle", "dircodigopostal", "dirnumero"
        ]

class UpdatePlantaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Planta
        fields = [
            "codigo", "nombre", "descripcion", "telefono",
            "dircalle", "dircodigopostal", "dirnumero"
        ]


# ==========================================================
# AREA
# ==========================================================
class ListAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = "__all__"

class DetailAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = "__all__"

class CreateAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ["codigo", "nombre", "descripcion", "telefono", "planta"]

class UpdateAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ["codigo", "nombre", "descripcion", "telefono", "planta"]


# ==========================================================
# EDO MAQUINA
# ==========================================================
class ListEdoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EdoMaquina
        fields = "__all__"

class DetailEdoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EdoMaquina
        fields = "__all__"

class CreateEdoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EdoMaquina
        fields = ["codigo", "nombre", "descripcion"]

class UpdateEdoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EdoMaquina
        fields = ["codigo", "nombre", "descripcion"]


# ==========================================================
# LINEA
# ==========================================================
class ListLineaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Linea
        fields = "__all__"

class DetailLineaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Linea
        fields = "__all__"

class CreateLineaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Linea
        fields = ["codigo", "nombre", "descripcion", "telefono", "area"]

class UpdateLineaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Linea
        fields = ["codigo", "nombre", "descripcion", "telefono", "area"]


# ==========================================================
# MARCA
# ==========================================================
class ListMarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = "__all__"

class DetailMarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = "__all__"

class CreateMarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = ["clave", "nombre", "descripcion"]

class UpdateMarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = ["clave", "nombre", "descripcion"]


# ==========================================================
# MODELO
# ==========================================================
class ListModeloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modelo
        fields = "__all__"

class DetailModeloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modelo
        fields = "__all__"

class CreateModeloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modelo
        fields = ["codigo", "nombre", "descripcion", "marca"]

class UpdateModeloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modelo
        fields = ["codigo", "nombre", "descripcion", "marca"]


# ==========================================================
# TIPO MAQUINA
# ==========================================================
class ListTipoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoMaquina
        fields = "__all__"

class DetailTipoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoMaquina
        fields = "__all__"

class CreateTipoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoMaquina
        fields = ["nombre", "descripcion"]

class UpdateTipoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoMaquina
        fields = ["nombre", "descripcion"]


# ==========================================================
# MAQUINA
# ==========================================================
class ListMaquinaSerializer(serializers.ModelSerializer):
    estado_maquina = serializers.StringRelatedField()
    tipo_maquina = serializers.StringRelatedField()
    linea = serializers.StringRelatedField()

    class Meta:
        model = Maquina
        fields = "__all__"

class DetailMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Maquina
        fields = "__all__"

class ValidarTipoMaquinaAreaMixin:
    """Bloquea guardar una máquina cuyo tipo_maquina no sea compatible con el
    área de la línea elegida. El getattr(self.instance, ...) cubre el caso de
    un PATCH parcial donde `linea` o `tipo_maquina` no vienen en el payload."""

    def validate(self, datos):
        linea = datos.get("linea") or getattr(self.instance, "linea", None)
        tipo_maquina = datos.get("tipo_maquina") or getattr(self.instance, "tipo_maquina", None)
        if linea and tipo_maquina:
            restringido = TipoMaquinaArea.objects.filter(tipo_maquina=tipo_maquina).exists()
            if restringido and not TipoMaquinaArea.objects.filter(tipo_maquina=tipo_maquina, area=linea.area).exists():
                raise serializers.ValidationError({
                    "tipo_maquina": "Este tipo de máquina no es compatible con el área de esa línea."
                })
        return datos


class CreateMaquinaSerializer(ValidarTipoMaquinaAreaMixin, serializers.ModelSerializer):
    imagen = serializers.FileField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Maquina
        fields = [
            "codigo", "numeroserie", "nombre", "descripcion", "imagen_url",
            "imagen",
            "modelo_3d", "fechainstalacion", "linea", "marca", "modelo",
            "estado_maquina", "tipo_maquina"
        ]

    def create(self, validated_data):
        imagen_file = validated_data.pop("imagen", None)
        if imagen_file:
            carpeta = os.path.join(settings.MEDIA_ROOT, "maquinaria")
            os.makedirs(carpeta, exist_ok=True)
            ruta = os.path.join(carpeta, imagen_file.name)
            with open(ruta, "wb+") as dest:
                for chunk in imagen_file.chunks():
                    dest.write(chunk)
            validated_data["imagen_url"] = f"maquinaria/{imagen_file.name}"
        return super().create(validated_data)

class UpdateMaquinaSerializer(serializers.ModelSerializer):
    imagen = serializers.FileField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Maquina
        fields = [
            "codigo", "numeroserie", "nombre", "descripcion", "imagen_url",
            "imagen",
            "modelo_3d", "fechainstalacion", "linea", "marca", "modelo",
            "estado_maquina", "tipo_maquina"
        ]

    def update(self, instance, validated_data):
            imagen_file = validated_data.pop("imagen", None)
            if imagen_file:
                carpeta = os.path.join(settings.MEDIA_ROOT, "maquinaria")
                os.makedirs(carpeta, exist_ok=True)
                ruta = os.path.join(carpeta, imagen_file.name)
                with open(ruta, "wb+") as dest:
                    for chunk in imagen_file.chunks():
                        dest.write(chunk)
                validated_data["imagen_url"] = f"maquinaria/{imagen_file.name}"

            # estado_maquina NUNCA se pisa directo aquí: si viene en el payload
            # (p. ej. desde Gestión) se saca del validated_data y se enruta por
            # cambiar_estado_maquina(), para que HISTORIAL_ESTADO_MAQUINA y
            # REGISTRO_OPS (y con ello MTBF/MTTR/Disponibilidad) queden
            # consistentes sin importar que el cambio venga de Gestión o de los
            # endpoints dedicados (validar/deshabilitar/reactivar).
            nuevo_estado = validated_data.pop("estado_maquina", None)
            if nuevo_estado is not None:
                nuevo_estado_id = nuevo_estado.pk if hasattr(nuevo_estado, "pk") else nuevo_estado
                if nuevo_estado_id != instance.estado_maquina_id:
                    from django.core.exceptions import ValidationError as DjangoValidationError
                    from .services import cambiar_estado_maquina
                    try:
                        cambiar_estado_maquina(instance.codigo, nuevo_estado_id, referencia_tipo="gestion")
                    except DjangoValidationError as e:
                        raise serializers.ValidationError({"estado_maquina": e.messages if hasattr(e, "messages") else str(e)})
                    instance.refresh_from_db()

            return super().update(instance, validated_data)


# ==========================================================
# OTROS MÓDULOS (Piezas, Refacciones, Indicadores, Reportes, Órdenes)
# ==========================================================
#class PiezaSerializer(serializers.ModelSerializer):
#    class Meta:
#        model = Pieza
#        fields = "__all__"

class RefaccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refaccion
        fields = "__all__"

#class IndicadorSerializer(serializers.ModelSerializer):
#    class Meta:
#        model = Indicador
#        fields = "__all__"

class ReporteFallaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReporteFalla
        fields = "__all__"

class OrdenMantenimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdenMantenimiento
        fields = "__all__"