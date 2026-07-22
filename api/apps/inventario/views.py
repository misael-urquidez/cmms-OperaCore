from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from . import models
from . import serializers


# ------------ PING & CATÁLOGOS AGREGADOS ----------------------------------
class PingAPIView(APIView):
    """Endpoint de prueba: confirma que el módulo Inventario responde."""
    def get(self, request):
        return Response({"modulo": "inventario", "status": "ok"}, status=status.HTTP_200_OK)


class CatalogosInventarioAPIView(APIView):
    """Junta los catálogos principales para los formularios de registro."""
    def get(self, request):
        data = {
            "clasificaciones": serializers.ListClasificacionSerializer(
                models.Clasificacion.objects.all(), many=True
            ).data,
            "estados_herramienta": serializers.ListEdoHerramientaSerializer(
                models.EdoHerramienta.objects.all(), many=True
            ).data,
            "estados_pieza": serializers.ListEdoPiezaSerializer(
                models.EdoPieza.objects.all(), many=True
            ).data,
            "estados_refaccion": serializers.ListEdoRefaccionSerializer(
                models.EdoRefaccion.objects.all(), many=True
            ).data,
            "tipos_herramienta": serializers.ListTipoHerramientaSerializer(
                models.TipoHerramienta.objects.all(), many=True
            ).data,
            "tipos_pieza": serializers.ListTipoPiezaSerializer(
                models.TipoPieza.objects.all(), many=True
            ).data,
            "tipos_refaccion": serializers.ListTipoRefaccionSerializer(
                models.TipoRefaccion.objects.all(), many=True
            ).data,
            "proveedores": serializers.ListProveedorSerializer(
                models.Proveedor.objects.all(), many=True
            ).data,
        }
        return Response(data, status=status.HTTP_200_OK)


# ------------ CLASIFICACIÓN ------------------------------------------------
class ClasificacionListAPIView(generics.ListAPIView):
    queryset = models.Clasificacion.objects.all().order_by("nombre")
    serializer_class = serializers.ListClasificacionSerializer


class ClasificacionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Clasificacion.objects.all()
    serializer_class = serializers.DetailClasificacionSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateClasificacionSerializer
        return serializers.DetailClasificacionSerializer


class ClasificacionCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateClasificacionSerializer


# ------------ EDO HERRAMIENTA ----------------------------------------------
class EdoHerramientaListAPIView(generics.ListAPIView):
    queryset = models.EdoHerramienta.objects.all().order_by("nombre")
    serializer_class = serializers.ListEdoHerramientaSerializer


class EdoHerramientaDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.EdoHerramienta.objects.all()
    serializer_class = serializers.DetailEdoHerramientaSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateEdoHerramientaSerializer
        return serializers.DetailEdoHerramientaSerializer


class EdoHerramientaCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateEdoHerramientaSerializer


# ------------ EDO PIEZA ----------------------------------------------------
class EdoPiezaListAPIView(generics.ListAPIView):
    queryset = models.EdoPieza.objects.all().order_by("nombre")
    serializer_class = serializers.ListEdoPiezaSerializer


class EdoPiezaDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.EdoPieza.objects.all()
    serializer_class = serializers.DetailEdoPiezaSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateEdoPiezaSerializer
        return serializers.DetailEdoPiezaSerializer


class EdoPiezaCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateEdoPiezaSerializer


# ------------ EDO REFACCION ------------------------------------------------
class EdoRefaccionListAPIView(generics.ListAPIView):
    queryset = models.EdoRefaccion.objects.all().order_by("nombre")
    serializer_class = serializers.ListEdoRefaccionSerializer


class EdoRefaccionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.EdoRefaccion.objects.all()
    serializer_class = serializers.DetailEdoRefaccionSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateEdoRefaccionSerializer
        return serializers.DetailEdoRefaccionSerializer


class EdoRefaccionCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateEdoRefaccionSerializer


# ------------ TIPO HERRAMIENTA ---------------------------------------------
class TipoHerramientaListAPIView(generics.ListAPIView):
    queryset = models.TipoHerramienta.objects.all().order_by("nombre")
    serializer_class = serializers.ListTipoHerramientaSerializer


class TipoHerramientaDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.TipoHerramienta.objects.all()
    serializer_class = serializers.DetailTipoHerramientaSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateTipoHerramientaSerializer
        return serializers.DetailTipoHerramientaSerializer


class TipoHerramientaCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateTipoHerramientaSerializer


# ------------ TIPO PIEZA ---------------------------------------------------
class TipoPiezaListAPIView(generics.ListAPIView):
    queryset = models.TipoPieza.objects.all().order_by("nombre")
    serializer_class = serializers.ListTipoPiezaSerializer


class TipoPiezaDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.TipoPieza.objects.all()
    serializer_class = serializers.DetailTipoPiezaSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateTipoPiezaSerializer
        return serializers.DetailTipoPiezaSerializer


class TipoPiezaCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateTipoPiezaSerializer


# ------------ TIPO REFACCION -----------------------------------------------
class TipoRefaccionListAPIView(generics.ListAPIView):
    queryset = models.TipoRefaccion.objects.all().order_by("nombre")
    serializer_class = serializers.ListTipoRefaccionSerializer


class TipoRefaccionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.TipoRefaccion.objects.all()
    serializer_class = serializers.DetailTipoRefaccionSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateTipoRefaccionSerializer
        return serializers.DetailTipoRefaccionSerializer


class TipoRefaccionCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateTipoRefaccionSerializer


# ------------ PROVEEDORES --------------------------------------------------
class ProveedorListAPIView(generics.ListAPIView):
    queryset = models.Proveedor.objects.all().order_by("razonsocial")
    serializer_class = serializers.ListProveedorSerializer


class ProveedorDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Proveedor.objects.all()
    serializer_class = serializers.DetailProveedorSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateProveedorSerializer
        return serializers.DetailProveedorSerializer


class ProveedorCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateProveedorSerializer


# ------------ HERRAMIENTAS -------------------------------------------------
class HerramientaListAPIView(generics.ListAPIView):
    queryset = models.Herramienta.objects.select_related("tipo_herramienta").order_by("nombre")
    serializer_class = serializers.ListHerramientaSerializer


class HerramientaDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Herramienta.objects.select_related("tipo_herramienta")
    serializer_class = serializers.DetailHerramientaSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateHerramientaSerializer
        return serializers.DetailHerramientaSerializer


class HerramientaCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateHerramientaSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        herramienta = serializer.save()
        data = serializers.DetailHerramientaSerializer(herramienta).data
        return Response(data, status=status.HTTP_201_CREATED)


# ------------ PIEZAS -------------------------------------------------------
class PiezaListAPIView(generics.ListAPIView):
    queryset = models.Pieza.objects.select_related("maquina", "edo_pieza", "tipo_pieza").order_by("nombre")
    serializer_class = serializers.ListPiezaSerializer


class PiezaDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Pieza.objects.select_related("maquina", "edo_pieza", "tipo_pieza")
    serializer_class = serializers.DetailPiezaSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdatePiezaSerializer
        return serializers.DetailPiezaSerializer


class PiezaCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreatePiezaSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pieza = serializer.save()
        data = serializers.DetailPiezaSerializer(pieza).data
        return Response(data, status=status.HTTP_201_CREATED)


# ------------ REFACCIONES --------------------------------------------------
class RefaccionListAPIView(generics.ListAPIView):
    queryset = models.Refaccion.objects.select_related("proveedor", "tipo_refaccion", "clasificacion").order_by("nombre")
    serializer_class = serializers.ListRefaccionSerializer


class RefaccionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Refaccion.objects.select_related("proveedor", "tipo_refaccion", "clasificacion")
    serializer_class = serializers.DetailRefaccionSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateRefaccionSerializer
        return serializers.DetailRefaccionSerializer


class RefaccionCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateRefaccionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refaccion = serializer.save()
        data = serializers.DetailRefaccionSerializer(refaccion).data
        return Response(data, status=status.HTTP_201_CREATED)


# ------------ TABLAS DE RELACION / INTERMEDIAS (llave compuesta) ---------
# Estas 3 tienen PK compuesta en la BD (ver Meta.unique_together en
# models.py). DRF no soporta lookup_field de varias columnas, asi que el
# Detail busca el objeto a mano con get_object_or_404 usando los dos
# segmentos de la URL. Cada Detail es independiente, no comparten mixin
# a proposito (para que se puedan tocar por separado sin efectos cruzados).

class RefaccMaquiListAPIView(generics.ListAPIView):
    queryset = models.RefaccMaqui.objects.all()
    serializer_class = serializers.ListRefaccMaquiSerializer


class RefaccMaquiCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateRefaccMaquiSerializer


class RefaccMaquiDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.RefaccMaqui.objects.all()
    serializer_class = serializers.DetailRefaccMaquiSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateRefaccMaquiSerializer
        return serializers.DetailRefaccMaquiSerializer

    def get_object(self):
        obj = generics.get_object_or_404(
            self.get_queryset(),
            maquina=self.kwargs["maquina"],
            refaccion=self.kwargs["refaccion"],
        )
        self.check_object_permissions(self.request, obj)
        return obj


class EstadoHerramientaListAPIView(generics.ListAPIView):
    queryset = models.EstadoHerramienta.objects.all()
    serializer_class = serializers.ListEstadoHerramientaSerializer


class EstadoHerramientaCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateEstadoHerramientaSerializer


class EstadoHerramientaDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.EstadoHerramienta.objects.all()
    serializer_class = serializers.DetailEstadoHerramientaSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateEstadoHerramientaSerializer
        return serializers.DetailEstadoHerramientaSerializer

    def get_object(self):
        obj = generics.get_object_or_404(
            self.get_queryset(),
            herramienta=self.kwargs["herramienta"],
            edo_herramienta=self.kwargs["edo_herramienta"],
        )
        self.check_object_permissions(self.request, obj)
        return obj


class EstadoRefaccionListAPIView(generics.ListAPIView):
    queryset = models.EstadoRefaccion.objects.all()
    serializer_class = serializers.ListEstadoRefaccionSerializer


class EstadoRefaccionCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateEstadoRefaccionSerializer


class EstadoRefaccionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.EstadoRefaccion.objects.all()
    serializer_class = serializers.DetailEstadoRefaccionSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateEstadoRefaccionSerializer
        return serializers.DetailEstadoRefaccionSerializer

    def get_object(self):
        obj = generics.get_object_or_404(
            self.get_queryset(),
            estado_refaccion=self.kwargs["estado_refaccion"],
            refaccion=self.kwargs["refaccion"],
        )
        self.check_object_permissions(self.request, obj)
        return obj