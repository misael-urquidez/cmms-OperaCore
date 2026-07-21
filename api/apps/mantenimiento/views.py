from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from . import models
from . import serializers


class PingAPIView(APIView):
    """Endpoint de prueba: confirma que el modulo Mantenimiento responde."""

    def get(self, request):
        return Response({"modulo": "mantenimiento", "status": "ok"}, status=status.HTTP_200_OK)

# ------------ ESTADO ORDEN -----------------------------------------------------
class ListarEstadoOrdenAPIView(generics.ListAPIView):
    queryset = models.EstadoOrden.objects.all()
    serializer_class = serializers.ListEstadoOrdenSerializer

class DetailEstadoOrdenAPIView(generics.RetrieveAPIView):
    queryset = models.EstadoOrden.objects.all()
    serializer_class = serializers.DetailEstadoOrdenSerializer
    lookup_field = 'codigo'

class CrearEstadoOrdenAPIView(generics.CreateAPIView):
    queryset = models.EstadoOrden.objects.all()
    serializer_class = serializers.CreateEstadoOrdenSerializer

class UpdateEstadoOrdenAPIView(generics.UpdateAPIView):
    queryset = models.EstadoOrden.objects.all()
    serializer_class = serializers.UpdateEstadoOrdenSerializer
    lookup_field = 'codigo'


# ------------ TIPO MANTENIMIENTO -----------------------------------------------
class ListarTipoMantenimientoAPIView(generics.ListAPIView):
    queryset = models.TipoMantenimiento.objects.all()
    serializer_class = serializers.ListTipoMantenimientoSerializer

class DetailTipoMantenimientoAPIView(generics.RetrieveAPIView):
    queryset = models.TipoMantenimiento.objects.all()
    serializer_class = serializers.DetailTipoMantenimientoSerializer
    lookup_field = 'codigo'

class CrearTipoMantenimientoAPIView(generics.CreateAPIView):
    queryset = models.TipoMantenimiento.objects.all()
    serializer_class = serializers.CreateTipoMantenimientoSerializer

class UpdateTipoMantenimientoAPIView(generics.UpdateAPIView):
    queryset = models.TipoMantenimiento.objects.all()
    serializer_class = serializers.UpdateTipoMantenimientoSerializer
    lookup_field = 'codigo'


# ------------ TAREAS -----------------------------------------------------------
class ListarTareasAPIView(generics.ListAPIView):
    queryset = models.Tareas.objects.all()
    serializer_class = serializers.ListTareasSerializer

class DetailTareasAPIView(generics.RetrieveAPIView):
    queryset = models.Tareas.objects.all()
    serializer_class = serializers.DetailTareasSerializer

class CrearTareasAPIView(generics.CreateAPIView):
    queryset = models.Tareas.objects.all()
    serializer_class = serializers.CreateTareasSerializer

class UpdateTareasAPIView(generics.UpdateAPIView):
    queryset = models.Tareas.objects.all()
    serializer_class = serializers.UpdateTareasSerializer


# ------------ TIPO MOVIMIENTO --------------------------------------------------
class ListarTipoMovimientoAPIView(generics.ListAPIView):
    queryset = models.TipoMovimiento.objects.all()
    serializer_class = serializers.ListTipoMovimientoSerializer

class DetailTipoMovimientoAPIView(generics.RetrieveAPIView):
    queryset = models.TipoMovimiento.objects.all()
    serializer_class = serializers.DetailTipoMovimientoSerializer
    lookup_field = 'codigo'

class CrearTipoMovimientoAPIView(generics.CreateAPIView):
    queryset = models.TipoMovimiento.objects.all()
    serializer_class = serializers.CreateTipoMovimientoSerializer

class UpdateTipoMovimientoAPIView(generics.UpdateAPIView):
    queryset = models.TipoMovimiento.objects.all()
    serializer_class = serializers.UpdateTipoMovimientoSerializer
    lookup_field = 'codigo'


# ------------ ORDEN MANTENIMIENTO ----------------------------------------------
class ListarOrdenMantenimientoAPIView(generics.ListAPIView):
    queryset = models.OrdenMantenimiento.objects.all()
    serializer_class = serializers.ListOrdenMantenimientoSerializer

class DetailOrdenMantenimientoAPIView(generics.RetrieveAPIView):
    queryset = models.OrdenMantenimiento.objects.all()
    serializer_class = serializers.DetailOrdenMantenimientoSerializer
    lookup_field = 'folio'

class CrearOrdenMantenimientoAPIView(generics.CreateAPIView):
    queryset = models.OrdenMantenimiento.objects.all()
    serializer_class = serializers.CreateOrdenMantenimientoSerializer

class UpdateOrdenMantenimientoAPIView(generics.UpdateAPIView):
    queryset = models.OrdenMantenimiento.objects.all()
    serializer_class = serializers.UpdateOrdenMantenimientoSerializer
    lookup_field = 'folio'


# ------------ MOVIMIENTO -------------------------------------------------------
class ListarMovimientoAPIView(generics.ListAPIView):
    queryset = models.Movimiento.objects.all()
    serializer_class = serializers.ListMovimientoSerializer

class DetailMovimientoAPIView(generics.RetrieveAPIView):
    queryset = models.Movimiento.objects.all()
    serializer_class = serializers.DetailMovimientoSerializer

class CrearMovimientoAPIView(generics.CreateAPIView):
    queryset = models.Movimiento.objects.all()
    serializer_class = serializers.CreateMovimientoSerializer

class UpdateMovimientoAPIView(generics.UpdateAPIView):
    queryset = models.Movimiento.objects.all()
    serializer_class = serializers.UpdateMovimientoSerializer


# ------------ TABLAS DE RELACION / INTERMEDIAS ---------------------------------
class ListarTareaOrdenAPIView(generics.ListAPIView):
    queryset = models.TareaOrden.objects.all()
    serializer_class = serializers.ListTareaOrdenSerializer

class DetailTareaOrdenAPIView(generics.RetrieveAPIView):
    queryset = models.TareaOrden.objects.all()
    serializer_class = serializers.DetailTareaOrdenSerializer
    lookup_field = 'tarea'

class CrearTareaOrdenAPIView(generics.CreateAPIView):
    queryset = models.TareaOrden.objects.all()
    serializer_class = serializers.CreateTareaOrdenSerializer

class UpdateTareaOrdenAPIView(generics.UpdateAPIView):
    queryset = models.TareaOrden.objects.all()
    serializer_class = serializers.UpdateTareaOrdenSerializer
    lookup_field = 'tarea'


class ListarHerraOrdenAPIView(generics.ListAPIView):
    queryset = models.HerraOrden.objects.all()
    serializer_class = serializers.ListHerraOrdenSerializer

class DetailHerraOrdenAPIView(generics.RetrieveAPIView):
    queryset = models.HerraOrden.objects.all()
    serializer_class = serializers.DetailHerraOrdenSerializer
    lookup_field = 'herramienta'

class CrearHerraOrdenAPIView(generics.CreateAPIView):
    queryset = models.HerraOrden.objects.all()
    serializer_class = serializers.CreateHerraOrdenSerializer

class UpdateHerraOrdenAPIView(generics.UpdateAPIView):
    queryset = models.HerraOrden.objects.all()
    serializer_class = serializers.UpdateHerraOrdenSerializer
    lookup_field = 'herramienta'


class ListarTrabaOrdePersonalAPIView(generics.ListAPIView):
    queryset = models.TrabaOrdePersonal.objects.all()
    serializer_class = serializers.ListTrabaOrdePersonalSerializer

class DetailTrabaOrdePersonalAPIView(generics.RetrieveAPIView):
    queryset = models.TrabaOrdePersonal.objects.all()
    serializer_class = serializers.DetailTrabaOrdePersonalSerializer
    lookup_field = 'trabajador'

class CrearTrabaOrdePersonalAPIView(generics.CreateAPIView):
    queryset = models.TrabaOrdePersonal.objects.all()
    serializer_class = serializers.CreateTrabaOrdePersonalSerializer

class UpdateTrabaOrdePersonalAPIView(generics.UpdateAPIView):
    queryset = models.TrabaOrdePersonal.objects.all()
    serializer_class = serializers.UpdateTrabaOrdePersonalSerializer
    lookup_field = 'trabajador'
