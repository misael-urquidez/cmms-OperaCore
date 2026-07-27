from django.core.exceptions import ValidationError
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import models
from .models import Maquina
from .serializers import *
from .services import cambiar_estado_maquina


class PingAPIView(APIView):
    """Endpoint de prueba: confirma que el módulo Maquinaria responde."""

    def get(self, request):
        return Response({"modulo": "maquinaria", "status": "ok"}, status=status.HTTP_200_OK)


# ==========================================================
# PLANTA
# ==========================================================
class ListarPlantaAPIView(generics.ListAPIView):
    queryset = models.Planta.objects.all()
    serializer_class = ListPlantaSerializer

class DetailPlantaAPIView(generics.RetrieveAPIView):
    queryset = models.Planta.objects.all()
    serializer_class = DetailPlantaSerializer
    lookup_field = 'codigo'

class CrearPlantaAPIView(generics.CreateAPIView):
    queryset = models.Planta.objects.all()
    serializer_class = CreatePlantaSerializer

class UpdatePlantaAPIView(generics.UpdateAPIView):
    queryset = models.Planta.objects.all()
    serializer_class = UpdatePlantaSerializer
    lookup_field = 'codigo'


# ==========================================================
# AREA
# ==========================================================
class ListarAreaAPIView(generics.ListAPIView):
    queryset = models.Area.objects.all()
    serializer_class = ListAreaSerializer

class DetailAreaAPIView(generics.RetrieveAPIView):
    queryset = models.Area.objects.all()
    serializer_class = DetailAreaSerializer
    lookup_field = 'codigo'

class CrearAreaAPIView(generics.CreateAPIView):
    queryset = models.Area.objects.all()
    serializer_class = CreateAreaSerializer

class UpdateAreaAPIView(generics.UpdateAPIView):
    queryset = models.Area.objects.all()
    serializer_class = UpdateAreaSerializer
    lookup_field = 'codigo'


# ==========================================================
# EDO MAQUINA
# ==========================================================
class ListarEdoMaquinaAPIView(generics.ListAPIView):
    queryset = models.EdoMaquina.objects.all()
    serializer_class = ListEdoMaquinaSerializer

class DetailEdoMaquinaAPIView(generics.RetrieveAPIView):
    queryset = models.EdoMaquina.objects.all()
    serializer_class = DetailEdoMaquinaSerializer
    lookup_field = 'codigo'

class CrearEdoMaquinaAPIView(generics.CreateAPIView):
    queryset = models.EdoMaquina.objects.all()
    serializer_class = CreateEdoMaquinaSerializer

class UpdateEdoMaquinaAPIView(generics.UpdateAPIView):
    queryset = models.EdoMaquina.objects.all()
    serializer_class = UpdateEdoMaquinaSerializer
    lookup_field = 'codigo'


# ==========================================================
# LINEA
# ==========================================================
class ListarLineaAPIView(generics.ListAPIView):
    queryset = models.Linea.objects.all()
    serializer_class = ListLineaSerializer

class DetailLineaAPIView(generics.RetrieveAPIView):
    queryset = models.Linea.objects.all()
    serializer_class = DetailLineaSerializer
    lookup_field = 'codigo'

class CrearLineaAPIView(generics.CreateAPIView):
    queryset = models.Linea.objects.all()
    serializer_class = CreateLineaSerializer

class UpdateLineaAPIView(generics.UpdateAPIView):
    queryset = models.Linea.objects.all()
    serializer_class = UpdateLineaSerializer
    lookup_field = 'codigo'


# ==========================================================
# MARCA
# ==========================================================
class ListarMarcaAPIView(generics.ListAPIView):
    queryset = models.Marca.objects.all()
    serializer_class = ListMarcaSerializer

class DetailMarcaAPIView(generics.RetrieveAPIView):
    queryset = models.Marca.objects.all()
    serializer_class = DetailMarcaSerializer
    lookup_field = 'clave'

class CrearMarcaAPIView(generics.CreateAPIView):
    queryset = models.Marca.objects.all()
    serializer_class = CreateMarcaSerializer

class UpdateMarcaAPIView(generics.UpdateAPIView):
    queryset = models.Marca.objects.all()
    serializer_class = UpdateMarcaSerializer
    lookup_field = 'clave'


# ==========================================================
# MODELO
# ==========================================================
class ListarModeloAPIView(generics.ListAPIView):
    queryset = models.Modelo.objects.all()
    serializer_class = ListModeloSerializer

class DetailModeloAPIView(generics.RetrieveAPIView):
    queryset = models.Modelo.objects.all()
    serializer_class = DetailModeloSerializer
    lookup_field = 'codigo'

class CrearModeloAPIView(generics.CreateAPIView):
    queryset = models.Modelo.objects.all()
    serializer_class = CreateModeloSerializer

class UpdateModeloAPIView(generics.UpdateAPIView):
    queryset = models.Modelo.objects.all()
    serializer_class = UpdateModeloSerializer
    lookup_field = 'codigo'


# ==========================================================
# TIPO MAQUINA
# ==========================================================
class ListarTipoMaquinaAPIView(generics.ListAPIView):
    queryset = models.TipoMaquina.objects.all()
    serializer_class = ListTipoMaquinaSerializer

class DetailTipoMaquinaAPIView(generics.RetrieveAPIView):
    queryset = models.TipoMaquina.objects.all()
    serializer_class = DetailTipoMaquinaSerializer

class CrearTipoMaquinaAPIView(generics.CreateAPIView):
    queryset = models.TipoMaquina.objects.all()
    serializer_class = CreateTipoMaquinaSerializer

class UpdateTipoMaquinaAPIView(generics.UpdateAPIView):
    queryset = models.TipoMaquina.objects.all()
    serializer_class = UpdateTipoMaquinaSerializer


# ==========================================================
# MAQUINA
# ==========================================================
class ListarMaquinaAPIView(generics.ListAPIView):
    """Retorna un listado JSON de todas las máquinas usando ListMaquinaSerializer."""
    queryset = Maquina.objects.all()
    serializer_class = ListMaquinaSerializer

class DetailMaquinaAPIView(generics.RetrieveAPIView):
    """Retorna el detalle completo en JSON de una máquina por su código."""
    queryset = Maquina.objects.all()
    serializer_class = DetailMaquinaSerializer
    lookup_field = 'codigo'

class CrearMaquinaAPIView(generics.CreateAPIView):
    """Permite registrar una nueva máquina mediante la API REST."""
    queryset = Maquina.objects.all()
    serializer_class = CreateMaquinaSerializer

class UpdateMaquinaAPIView(generics.UpdateAPIView):
    """Permite actualizar la información de una máquina existente."""
    queryset = Maquina.objects.all()
    serializer_class = UpdateMaquinaSerializer
    lookup_field = 'codigo'


# ==========================================================
# CAMBIOS DE ESTADO MANUALES (nuevo)
# ==========================================================
class ValidarMaquinaAPIView(APIView):
    """ESPER -> OPERA. El admin/encargado valida que la reparación quedó bien."""
    def patch(self, request, codigo):
        try:
            maquina = cambiar_estado_maquina(codigo, "OPERA", "manual", None)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=400)
        return Response({"codigo": maquina.codigo, "estado_maquina": maquina.estado_maquina_id})


class DeshabilitarMaquinaAPIView(APIView):
    """OPERA -> DESHA."""
    def patch(self, request, codigo):
        try:
            maquina = cambiar_estado_maquina(codigo, "DESHA", "manual", None)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=400)
        return Response({"codigo": maquina.codigo, "estado_maquina": maquina.estado_maquina_id})


class ReactivarMaquinaAPIView(APIView):
    """DESHA -> OPERA."""
    def patch(self, request, codigo):
        try:
            maquina = cambiar_estado_maquina(codigo, "OPERA", "manual", None)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=400)
        return Response({"codigo": maquina.codigo, "estado_maquina": maquina.estado_maquina_id})