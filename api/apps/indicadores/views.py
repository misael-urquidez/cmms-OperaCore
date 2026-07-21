from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from . import models
from . import serializers


class PingAPIView(APIView):
    """Endpoint de prueba: confirma que el modulo Indicadores responde."""

    def get(self, request):
        return Response({"modulo": "indicadores", "status": "ok"}, status=status.HTTP_200_OK)

# ------------ INDICADOR --------------------------------------------------------
class ListarIndicadorAPIView(generics.ListAPIView):
    queryset = models.Indicador.objects.all()
    serializer_class = serializers.ListIndicadorSerializer

class DetailIndicadorAPIView(generics.RetrieveAPIView):
    queryset = models.Indicador.objects.all()
    serializer_class = serializers.DetailIndicadorSerializer

class CrearIndicadorAPIView(generics.CreateAPIView):
    queryset = models.Indicador.objects.all()
    serializer_class = serializers.CreateIndicadorSerializer

class UpdateIndicadorAPIView(generics.UpdateAPIView):
    queryset = models.Indicador.objects.all()
    serializer_class = serializers.UpdateIndicadorSerializer
