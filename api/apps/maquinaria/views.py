from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Maquina
from .serializers import *


class PingAPIView(APIView):
    """Endpoint de prueba: confirma que el módulo Maquinaria responde."""

    def get(self, request):
        return Response({"modulo": "maquinaria", "status": "ok"}, status=status.HTTP_200_OK)


# ======================================
# API LISTADO DE MAQUINAS
# ======================================

class ListMaquinariaAPIView(generics.ListAPIView):
    """Retorna un listado JSON de todas las máquinas usando ListMaquinaSerializer."""
    queryset = Maquina.objects.all()
    serializer_class = ListMaquinaSerializer


# ======================================
# API DETALLE DE MAQUINA
# ======================================

class DetailMaquinariaAPIView(generics.RetrieveAPIView):
    """Retorna el detalle completo en JSON de una máquina por su código (ej. MAQ001)."""
    queryset = Maquina.objects.all()
    serializer_class = DetailMaquinaSerializer
    lookup_field = "codigo"

class CreateMaquinariaAPIView(generics.CreateAPIView):
    """Permite registrar una nueva máquina mediante la API REST."""
    queryset = Maquina.objects.all()
    serializer_class = CreateMaquinaSerializer