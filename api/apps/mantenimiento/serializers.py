from rest_framework import serializers
from . import models

# Mismo patron que maquinaria/inventario/fallas: List (columnas resumidas),
# Detail (todos los campos, se usa tambien para editar via PUT/PATCH),
# Create (los campos que el usuario llena al dar de alta).

# ------------ ESTADO_ORDEN --------------------------------------------
class ListEstadoOrdenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EstadoOrden
        fields = ["codigo", "nombre"]


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
        fields = ["codigo", "nombre"]


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
        fields = ["numeroregistro", "instruccion", "actividad"]


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
        fields = ["codigo", "descripcion"]


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
        fields = ["tarea", "orden_mantenimiento", "fechainicio", "verificacion"]


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
        fields = ["herramienta", "orden_mantenimiento"]


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
        fields = ["trabajador", "orden_mantenimiento"]


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
