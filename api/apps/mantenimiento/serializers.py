from rest_framework import serializers
from apps.fallas.models import ReporteFalla
from apps.inventario.models import Herramienta, Pieza, Refaccion
from apps.usuarios.models import Trabajador
from . import models


def _recalcular_porcentaje(orden):
    """Porcentaje de avance de la orden = tareas verificadas / total * 100.
    Sin tareas queda NULL. Se actualiza con update() (sin save() del modelo)
    para no disparar el trigger de MTTR, que solo reacciona a fechaCierre."""
    total = orden.tareaorden_set.count()
    if total == 0:
        nuevo = None
    else:
        completadas = orden.tareaorden_set.filter(verificacion=1).count()
        nuevo = round(completadas * 100.0 / total)
    models.OrdenMantenimiento.objects.filter(pk=orden.pk).update(porcentaje=nuevo)
    return nuevo


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

    class Meta:
        model = models.Movimiento
        fields = ["tipoMovimiento", "fecha", "hora", "descripcion",
                  "orden_mantenimiento", "refaccion", "pieza"]


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
    tareas = serializers.SerializerMethodField()
    herramientas = serializers.SerializerMethodField()
    trabajadores = serializers.SerializerMethodField()

    class Meta(ListOrdenMantenimientoSerializer.Meta):
        fields = ["folio", "descripcion", "diagnostico", "notas", "fechaprogramada", "fechacreacion", "horacreacion", "fechacierre", "horacierre", "horasintervenidas", "porcentaje", "maquina", "maquina_nombre", "trabajador", "trabajador_nombre", "reporte_falla", "reporte_falla_asunto", "tipo_mantenimiento", "tipo_mantenimiento_nombre", "estado_orden", "estado_orden_nombre", "tareas", "herramientas", "trabajadores"]

    def get_tareas(self, obj):
        return [
            {"numeroregistro": to.tarea.numeroregistro, "instruccion": to.tarea.instruccion, "verificacion": bool(to.verificacion)}
            for to in obj.tareaorden_set.select_related("tarea").order_by("tarea__numeroregistro")
        ]

    def get_herramientas(self, obj):
        return [
            {"numeroregistro": ho.herramienta.numeroregistro, "nombre": ho.herramienta.nombre}
            for ho in obj.herraorden_set.select_related("herramienta").order_by("herramienta__numeroregistro")
        ]

    def get_trabajadores(self, obj):
        return [
            {"numeroNomina": tp.trabajador.numeroNomina, "nombre": tp.trabajador.nombre, "apellidoPat": tp.trabajador.apellidoPat}
            for tp in obj.trabaordepersonal_set.select_related("trabajador").order_by("trabajador__numeroNomina")
        ]


class CreateOrdenMantenimientoSerializer(serializers.ModelSerializer):
    tareas = serializers.ListField(child=serializers.IntegerField(), required=False, write_only=True, allow_empty=True)
    herramientas = serializers.ListField(child=serializers.IntegerField(), required=False, write_only=True, allow_empty=True)
    trabajadores = serializers.ListField(child=serializers.CharField(), required=False, write_only=True, allow_empty=True)

    class Meta:
        model = models.OrdenMantenimiento
        fields = ["descripcion", "fechaprogramada", "maquina", "trabajador", "reporte_falla", "tipo_mantenimiento", "notas", "tareas", "herramientas", "trabajadores"]
        extra_kwargs = {"trabajador": {"required": False, "allow_null": True}, "reporte_falla": {"required": False, "allow_null": True}, "notas": {"required": False, "allow_null": True}, "fechaprogramada": {"required": False, "allow_null": True}}

    def validate(self, data):
        reporte = data.get("reporte_falla")
        if reporte is not None:
            maquina = data.get("maquina")
            if maquina and reporte.maquina_id != maquina.codigo:
                raise serializers.ValidationError({"reporte_falla": "El reporte de falla no pertenece a la máquina seleccionada."})
            if models.OrdenMantenimiento.objects.filter(reporte_falla=reporte).exists():
                raise serializers.ValidationError({"reporte_falla": "Este reporte de falla ya está vinculado a otra orden."})
        for tid in data.get("tareas") or []:
            if not models.Tareas.objects.filter(numeroregistro=tid).exists():
                raise serializers.ValidationError({"tareas": f"La tarea {tid} no existe."})
        for hid in data.get("herramientas") or []:
            if not Herramienta.objects.filter(numeroregistro=hid).exists():
                raise serializers.ValidationError({"herramientas": f"La herramienta {hid} no existe."})
        for nomina in data.get("trabajadores") or []:
            if not Trabajador.objects.filter(numeroNomina=nomina).exists():
                raise serializers.ValidationError({"trabajadores": f"El trabajador {nomina} no existe."})
        return data

    def create(self, validated_data):
        from django.db import transaction
        from django.utils import timezone
        tareas_ids = validated_data.pop("tareas", None) or []
        herramientas_ids = validated_data.pop("herramientas", None) or []
        trabajadores_ids = validated_data.pop("trabajadores", None) or []
        ahora = timezone.localtime()
        folio = f"OMP{ahora:%y%m%d%H%M%S}"
        estado = models.EstadoOrden.objects.filter(codigo="PROGR" if validated_data.get("trabajador") else "SOLIC").first()
        with transaction.atomic():
            orden = models.OrdenMantenimiento.objects.create(folio=folio, fechacreacion=ahora.date(), horacreacion=ahora.time(), estado_orden=estado, **validated_data)
            fechainicio = validated_data.get("fechaprogramada") or ahora.date()
            for tid in tareas_ids:
                models.TareaOrden.objects.create(tarea_id=tid, orden_mantenimiento=orden, fechainicio=fechainicio, horainicio=ahora.time())
            for hid in herramientas_ids:
                models.HerraOrden.objects.create(herramienta_id=hid, orden_mantenimiento=orden)
            principal = validated_data.get("trabajador")
            for nomina in trabajadores_ids:
                if principal and nomina == principal.numeroNomina:
                    continue
                models.TrabaOrdePersonal.objects.create(trabajador_id=nomina, orden_mantenimiento=orden)
        if tareas_ids:
            _recalcular_porcentaje(orden)
        return orden


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
    trabajador = serializers.PrimaryKeyRelatedField(queryset=Trabajador.objects.all(), required=False, allow_null=True)
    horasIntervenidas = serializers.FloatField(source="horasintervenidas", required=False, allow_null=True)
    tareas = serializers.ListField(child=serializers.IntegerField(), required=False, write_only=True, allow_empty=True)
    herramientas = serializers.ListField(child=serializers.IntegerField(), required=False, write_only=True, allow_empty=True)
    trabajadores = serializers.ListField(child=serializers.CharField(), required=False, write_only=True, allow_empty=True)

    class Meta:
        model = models.OrdenMantenimiento
        fields = ["descripcion", "fechaprogramada", "tipo_mantenimiento", "notas", "diagnostico", "trabajador", "horasIntervenidas", "tareas", "herramientas", "trabajadores"]

    def validate(self, data):
        for tid in data.get("tareas") or []:
            if not models.Tareas.objects.filter(numeroregistro=tid).exists():
                raise serializers.ValidationError({"tareas": f"La tarea {tid} no existe."})
        for hid in data.get("herramientas") or []:
            if not Herramienta.objects.filter(numeroregistro=hid).exists():
                raise serializers.ValidationError({"herramientas": f"La herramienta {hid} no existe."})
        for nomina in data.get("trabajadores") or []:
            if not Trabajador.objects.filter(numeroNomina=nomina).exists():
                raise serializers.ValidationError({"trabajadores": f"El trabajador {nomina} no existe."})
        return data

    def update(self, instance, validated_data):
        from django.db import transaction
        from django.utils import timezone
        tareas_ids = validated_data.pop("tareas", None)
        herramientas_ids = validated_data.pop("herramientas", None)
        trabajadores_ids = validated_data.pop("trabajadores", None)
        with transaction.atomic():
            for campo, valor in validated_data.items():
                setattr(instance, campo, valor)
            instance.save()
            # Semantica de reemplazo: si el cliente manda una lista, se borran
            # las filas de esa tabla puente y se re-insertan las enviadas.
            # Si no manda la clave, las asociaciones quedan intactas.
            if tareas_ids is not None:
                models.TareaOrden.objects.filter(orden_mantenimiento=instance).delete()
                fechainicio = instance.fechaprogramada or instance.fechacreacion
                for tid in tareas_ids:
                    models.TareaOrden.objects.create(tarea_id=tid, orden_mantenimiento=instance, fechainicio=fechainicio, horainicio=timezone.localtime().time())
            if herramientas_ids is not None:
                models.HerraOrden.objects.filter(orden_mantenimiento=instance).delete()
                for hid in herramientas_ids:
                    models.HerraOrden.objects.create(herramienta_id=hid, orden_mantenimiento=instance)
            if trabajadores_ids is not None:
                models.TrabaOrdePersonal.objects.filter(orden_mantenimiento=instance).delete()
                principal = instance.trabajador
                for nomina in trabajadores_ids:
                    if principal and nomina == principal.numeroNomina:
                        continue
                    models.TrabaOrdePersonal.objects.create(trabajador_id=nomina, orden_mantenimiento=instance)
        if tareas_ids is not None:
            _recalcular_porcentaje(instance)
        return instance
