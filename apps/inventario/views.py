from rest_framework import generics

from .models import Herramienta, Movimiento, Refaccion
from .serializers import (
    HerramientaDetailSerializer,
    HerramientaListSerializer,
    MovimientoCreateSerializer,
    RefaccionDetailSerializer,
    RefaccionListSerializer,
)


# ---------------------------------------------------------------------
# Refacción
# ---------------------------------------------------------------------

class ListRefaccionAPIView(generics.ListAPIView):
    """GET v1/refacciones/list/"""
    queryset = Refaccion.objects.select_related('proveedor').all()
    serializer_class = RefaccionListSerializer


class DetailRefaccionAPIView(generics.RetrieveAPIView):
    """GET v1/refacciones/<pk>/"""
    queryset = Refaccion.objects.select_related('proveedor').prefetch_related('estados__estado_refaccion')
    serializer_class = RefaccionDetailSerializer
    lookup_field = 'numero_registro'
    lookup_url_kwarg = 'pk'


# ---------------------------------------------------------------------
# Herramienta
# ---------------------------------------------------------------------

class ListHerramientaAPIView(generics.ListAPIView):
    """GET v1/herramientas/list/"""
    queryset = Herramienta.objects.select_related('tipo_herramienta').all()
    serializer_class = HerramientaListSerializer


class DetailHerramientaAPIView(generics.RetrieveAPIView):
    """GET v1/herramientas/<pk>/"""
    queryset = Herramienta.objects.select_related('tipo_herramienta').prefetch_related('estados__edo_herramienta')
    serializer_class = HerramientaDetailSerializer
    lookup_field = 'numero_registro'
    lookup_url_kwarg = 'pk'


# ---------------------------------------------------------------------
# Movimiento
# ---------------------------------------------------------------------

class CreateMovimientoAPIView(generics.CreateAPIView):
    """POST v2/movimientos/create/ -- registra entrada/salida y actualiza el stock."""
    queryset = Movimiento.objects.all()
    serializer_class = MovimientoCreateSerializer
