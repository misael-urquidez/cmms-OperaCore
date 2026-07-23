from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from . import models
from . import serializers


class PingAPIView(APIView):
    """Endpoint de prueba: confirma que el modulo Mantenimiento responde."""

    def get(self, request):
        return Response({"modulo": "mantenimiento", "status": "ok"}, status=status.HTTP_200_OK)


# ------------ ESTADO_ORDEN --------------------------------------------
class EstadoOrdenListAPIView(generics.ListAPIView):
    queryset = models.EstadoOrden.objects.all().order_by("nombre")
    serializer_class = serializers.ListEstadoOrdenSerializer


class EstadoOrdenCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateEstadoOrdenSerializer


class EstadoOrdenDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.EstadoOrden.objects.all()
    lookup_field = "codigo"

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return serializers.CreateEstadoOrdenSerializer
        return serializers.DetailEstadoOrdenSerializer


# ------------ TIPO_MANTENIMIENTO ---------------------------------------
class TipoMantenimientoListAPIView(generics.ListAPIView):
    queryset = models.TipoMantenimiento.objects.all().order_by("nombre")
    serializer_class = serializers.ListTipoMantenimientoSerializer


class TipoMantenimientoCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateTipoMantenimientoSerializer


class TipoMantenimientoDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.TipoMantenimiento.objects.all()
    lookup_field = "codigo"

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return serializers.CreateTipoMantenimientoSerializer
        return serializers.DetailTipoMantenimientoSerializer


# ------------ TAREAS -----------------------------------------------------
class TareasListAPIView(generics.ListAPIView):
    queryset = models.Tareas.objects.all().order_by("numeroregistro")
    serializer_class = serializers.ListTareasSerializer


class TareasCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateTareasSerializer


class TareasDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Tareas.objects.all()
    lookup_field = "numeroregistro"

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return serializers.CreateTareasSerializer
        return serializers.DetailTareasSerializer


# ------------ TIPO_MOVIMIENTO -------------------------------------------
class TipoMovimientoListAPIView(generics.ListAPIView):
    queryset = models.TipoMovimiento.objects.all().order_by("codigo")
    serializer_class = serializers.ListTipoMovimientoSerializer


class TipoMovimientoCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateTipoMovimientoSerializer


class TipoMovimientoDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.TipoMovimiento.objects.all()
    lookup_field = "codigo"

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return serializers.CreateTipoMovimientoSerializer
        return serializers.DetailTipoMovimientoSerializer


# ------------ TAREA_ORDEN (llave compuesta) ------------------------------
# PK real en BD: (tarea, orden_mantenimiento). Igual que en inventario,
# cada Detail resuelve su propio get_object a mano; no se comparte mixin
# entre tablas para que se puedan modificar por separado sin romper otras.
class TareaOrdenListAPIView(generics.ListAPIView):
    queryset = models.TareaOrden.objects.all()
    serializer_class = serializers.ListTareaOrdenSerializer


class TareaOrdenCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateTareaOrdenSerializer


class TareaOrdenDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.TareaOrden.objects.all()
    serializer_class = serializers.DetailTareaOrdenSerializer

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return serializers.UpdateTareaOrdenSerializer
        return serializers.DetailTareaOrdenSerializer

    def get_object(self):
        obj = generics.get_object_or_404(
            self.get_queryset(),
            tarea=self.kwargs["tarea"],
            orden_mantenimiento=self.kwargs["orden_mantenimiento"],
        )
        self.check_object_permissions(self.request, obj)
        return obj


# ------------ HERRA_ORDEN (llave compuesta) -------------------------------
class HerraOrdenListAPIView(generics.ListAPIView):
    queryset = models.HerraOrden.objects.all()
    serializer_class = serializers.ListHerraOrdenSerializer


class HerraOrdenCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateHerraOrdenSerializer


class HerraOrdenDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.HerraOrden.objects.all()
    serializer_class = serializers.DetailHerraOrdenSerializer

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return serializers.UpdateHerraOrdenSerializer
        return serializers.DetailHerraOrdenSerializer

    def get_object(self):
        obj = generics.get_object_or_404(
            self.get_queryset(),
            herramienta=self.kwargs["herramienta"],
            orden_mantenimiento=self.kwargs["orden_mantenimiento"],
        )
        self.check_object_permissions(self.request, obj)
        return obj


# ------------ TRABA_ORDE_PERSONAL (llave compuesta) -----------------------
class TrabaOrdePersonalListAPIView(generics.ListAPIView):
    queryset = models.TrabaOrdePersonal.objects.all()
    serializer_class = serializers.ListTrabaOrdePersonalSerializer


class TrabaOrdePersonalCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateTrabaOrdePersonalSerializer


class TrabaOrdePersonalDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.TrabaOrdePersonal.objects.all()
    serializer_class = serializers.DetailTrabaOrdePersonalSerializer

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return serializers.UpdateTrabaOrdePersonalSerializer
        return serializers.DetailTrabaOrdePersonalSerializer

    def get_object(self):
        obj = generics.get_object_or_404(
            self.get_queryset(),
            trabajador=self.kwargs["trabajador"],
            orden_mantenimiento=self.kwargs["orden_mantenimiento"],
        )
        self.check_object_permissions(self.request, obj)
        return obj


# ------------ ORDEN_MANTENIMIENTO -------------------------------------
class OrdenMantenimientoListAPIView(generics.ListAPIView):
    queryset = models.OrdenMantenimiento.objects.all().order_by("-fechacreacion", "-horacreacion")
    serializer_class = serializers.ListOrdenMantenimientoSerializer


class OrdenMantenimientoCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateOrdenMantenimientoSerializer


class OrdenMantenimientoDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.OrdenMantenimiento.objects.all()
    lookup_field = "folio"

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return serializers.CreateOrdenMantenimientoSerializer
        return serializers.DetailOrdenMantenimientoSerializer


# ------------ MOVIMIENTO -----------------------------------------------
class MovimientoListAPIView(generics.ListAPIView):
    queryset = models.Movimiento.objects.all().order_by("-fecha", "-hora")
    serializer_class = serializers.ListMovimientoSerializer


class MovimientoCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateMovimientoSerializer


class MovimientoDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Movimiento.objects.all()
    lookup_field = "numeroregistro"

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return serializers.CreateMovimientoSerializer
        return serializers.DetailMovimientoSerializer
