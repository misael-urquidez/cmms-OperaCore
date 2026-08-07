from rest_framework import serializers
from apps.fallas.models import ReporteFalla
from apps.inventario.models import Pieza, Refaccion
from . import models

# Mismo patron que maquinaria/inventario/fallas: List (columnas resumidas),
# Detail (todos los campos, se usa tambien para editar via PUT/PATCH),
# Create (los campos que el usuario llena al dar de alta).

# ------------ ESTADO_ORDEN --------------------------------------------
class ListEstadoOrdenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EstadoOrden
        fields = "__all__"


class DetailEstadoOrdenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EstadoOrden
        fields = "__all__"


class CreateEstadoOrdenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EstadoOrden
        fields = ["codigo", "nombre", "descripcion"]


# ------------ TIPO_MANTENIMIENTO ---------------------------------------
class ListTipoMantenimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoMantenimiento
        fields = "__all__"


class DetailTipoMantenimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoMantenimiento
        fields = "__all__"


class CreateTipoMantenimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoMantenimiento
        fields = ["codigo", "nombre", "descripcion"]


# ------------ TAREAS -----------------------------------------------------
class ListTareasSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tareas
        fields = "__all__"


class DetailTareasSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tareas
        fields = "__all__"


class CreateTareasSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tareas
        fields = ["instruccion", "actividad"]


# ------------ TIPO_MOVIMIENTO -------------------------------------------
class ListTipoMovimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoMovimiento
        fields = "__all__"


class DetailTipoMovimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoMovimiento
        fields = "__all__"


class CreateTipoMovimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoMovimiento
        fields = ["codigo", "descripcion"]


# ------------ TAREA_ORDEN (llave compuesta: tarea, orden_mantenimiento) --
class ListTareaOrdenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TareaOrden
        fields = "__all__"


# ------------ MOVIMIENTO ---------------------------------------------------
class ListMovimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Movimiento
        fields = "__all__"


class CreateMovimientoSerializer(serializers.ModelSerializer):
    tipoMovimiento = serializers.CharField(source="tipomovimiento")
    pieza_data = serializers.DictField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = models.Movimiento
        fields = ["tipoMovimiento", "fecha", "hora", "descripcion",
                  "orden_mantenimiento", "refaccion", "pieza", "pieza_data"]


class DetailTareaOrdenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TareaOrden
        fields = "__all__"


class CreateTareaOrdenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TareaOrden
        fields = [
            "tarea", "orden_mantenimiento", "fechainicio", "fechacierre",
            "horainicio", "horafin", "verificacion", "observaciones",
        ]


class UpdateTareaOrdenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TareaOrden
        fields = ["fechacierre", "horafin", "verificacion", "observaciones"]


# ------------ HERRA_ORDEN (llave compuesta: herramienta, orden_mantenimiento) --
class ListHerraOrdenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HerraOrden
        fields = "__all__"


class DetailHerraOrdenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HerraOrden
        fields = "__all__"


class CreateHerraOrdenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HerraOrden
        fields = ["herramienta", "orden_mantenimiento"]


class UpdateHerraOrdenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HerraOrden
        fields = ["herramienta", "orden_mantenimiento"]


# ------------ TRABA_ORDE_PERSONAL (llave compuesta: trabajador, orden_mantenimiento) --
class ListTrabaOrdePersonalSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TrabaOrdePersonal
        fields = "__all__"


class DetailTrabaOrdePersonalSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TrabaOrdePersonal
        fields = "__all__"


class CreateTrabaOrdePersonalSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TrabaOrdePersonal
        fields = ["trabajador", "orden_mantenimiento"]


class UpdateTrabaOrdePersonalSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TrabaOrdePersonal
        fields = ["trabajador", "orden_mantenimiento"]


# ------------ ORDEN_MANTENIMIENTO ---------------------------------------
class ListOrdenMantenimientoSerializer(serializers.ModelSerializer):
    maquina_nombre = serializers.CharField(source="maquina.nombre", read_only=True)
    trabajador_nombre = serializers.CharField(source="trabajador.nombre", read_only=True)
    tipo_mantenimiento_nombre = serializers.CharField(source="tipo_mantenimiento.nombre", read_only=True)
    estado_orden_nombre = serializers.CharField(source="estado_orden.nombre", read_only=True)
    reporte_falla_asunto = serializers.CharField(source="reporte_falla.asunto", read_only=True)

    class Meta:
        model = models.OrdenMantenimiento
        fields = ["folio", "descripcion", "fechacreacion", "horacreacion", "fechaprogramada", "fechacierre", "maquina", "maquina_nombre", "trabajador", "trabajador_nombre", "reporte_falla", "reporte_falla_asunto", "tipo_mantenimiento", "tipo_mantenimiento_nombre", "estado_orden", "estado_orden_nombre"]


class DetailOrdenMantenimientoSerializer(ListOrdenMantenimientoSerializer):
    class Meta(ListOrdenMantenimientoSerializer.Meta):
        fields = ["folio", "descripcion", "diagnostico", "notas", "fechaprogramada", "fechacreacion", "horacreacion", "fechacierre", "horacierre", "horasintervenidas", "porcentaje", "maquina", "maquina_nombre", "trabajador", "trabajador_nombre", "reporte_falla", "reporte_falla_asunto", "tipo_mantenimiento", "tipo_mantenimiento_nombre", "estado_orden", "estado_orden_nombre"]


class CreateOrdenMantenimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrdenMantenimiento
        fields = ["descripcion", "fechaprogramada", "maquina", "trabajador", "reporte_falla", "tipo_mantenimiento", "notas"]
        extra_kwargs = {"trabajador": {"required": False, "allow_null": True}, "reporte_falla": {"required": False, "allow_null": True}, "notas": {"required": False, "allow_null": True}, "fechaprogramada": {"required": False, "allow_null": True}}

    def validate(self, data):
        reporte = data.get("reporte_falla")
        if reporte is not None:
            maquina = data.get("maquina")
            if maquina and reporte.maquina_id != maquina.codigo:
                raise serializers.ValidationError({"reporte_falla": "El reporte de falla no pertenece a la máquina seleccionada."})
            if models.OrdenMantenimiento.objects.filter(reporte_falla=reporte).exists():
                raise serializers.ValidationError({"reporte_falla": "Este reporte de falla ya está vinculado a otra orden."})
        return data

    def create(self, validated_data):
        from django.utils import timezone
        ahora = timezone.localtime()
        folio = f"OMP{ahora:%y%m%d%H%M%S}"
        estado = models.EstadoOrden.objects.filter(codigo="PROGR" if validated_data.get("trabajador") else "SOLIC").first()
        return models.OrdenMantenimiento.objects.create(folio=folio, fechacreacion=ahora.date(), horacreacion=ahora.time(), estado_orden=estado, **validated_data)


# ------------ REPORTE_FALLA (solo para el selector "adjuntar reporte") --
class ReporteFallaDisponibleSerializer(serializers.ModelSerializer):
    tipo_severidad_nombre = serializers.CharField(source="tipo_severidad.nombre", read_only=True)
    estado_reporte_nombre = serializers.CharField(source="estado_reporte.nombre", read_only=True)

    class Meta:
        model = ReporteFalla
        fields = ["numeroRegistro", "asunto", "fechaCreacion", "horaCreacion", "tipo_severidad_nombre", "estado_reporte_nombre", "maquina"]


class AsignarTrabajadorOrdenSerializer(serializers.Serializer):
    trabajador = serializers.CharField()


class MovimientoCierreItemSerializer(serializers.Serializer):
    """Un renglon de 'refaccion instalada / pieza que reemplaza' capturado
    en el drawer al cerrar la orden. refaccion es obligatoria (siempre se
    instala algo); pieza es opcional (solo si habia una pieza fisica
    previa que salio de la maquina). Se valida que ambas existan en el
    catalogo para no reventar el INSERT."""
    refaccion = serializers.PrimaryKeyRelatedField(queryset=Refaccion.objects.all())
    pieza = serializers.PrimaryKeyRelatedField(
        queryset=Pieza.objects.all(), required=False, allow_null=True
    )


class CerrarOrdenSerializer(serializers.Serializer):
    diagnostico = serializers.CharField(max_length=500, required=False, allow_blank=True)
    notas = serializers.CharField(max_length=500, required=False, allow_blank=True)
    horasIntervenidas = serializers.FloatField(required=False, allow_null=True)
    # Lista opcional de refacciones/piezas registradas en el drawer de cierre.
    # Por cada item se generan HASTA dos movimientos (ver views.py):
    # un DESMO si vino "pieza" (la pieza fisica que salio de la maquina) y
    # siempre un INSTA para la refaccion que entro. Antes esto se mandaba
    # como peticiones sueltas desde el JS y solo se guardaba un INSTA
    # mezclando ambos datos; ahora viaja en la misma peticion de cierre y
    # se crea todo dentro de la misma transaccion atomica.
    movimientos = MovimientoCierreItemSerializer(many=True, required=False)


class UpdateOrdenMantenimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrdenMantenimiento
        fields = ["descripcion", "fechaprogramada", "tipo_mantenimiento", "notas", "diagnostico"]
