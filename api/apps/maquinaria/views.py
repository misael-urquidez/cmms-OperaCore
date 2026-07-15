from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from . import models
from . import serializers


class PingAPIView(APIView):
    """Endpoint de prueba: confirma que el modulo Maquinaria responde."""

    def get(self, request):
        return Response({"modulo": "maquinaria", "status": "ok"}, status=status.HTTP_200_OK)


# A partir de aqui sigue el patron de tu maestro cuando agregues modelos reales:
#
# class ListMaquinariaAPIView(generics.ListAPIView):
#     queryset = models.MiModelo.objects.all()
#     serializer_class = serializers.ListMaquinaSerializer
#
# class DetailMaquinariaAPIView(generics.RetrieveAPIView):
#     queryset = models.MiModelo.objects.all()
#     serializer_class = serializers.DetailMaquinaSerializer
#
# class CreateMaquinariaAPIView(generics.CreateAPIView):
#     serializer_class = serializers.CreateMaquinaSerializer
#
# class UpdateMaquinariaAPIView(generics.UpdateAPIView):
#     queryset = models.MiModelo.objects.all()
#     serializer_class = serializers.CreateMaquinaSerializer
#
# class DeleteMaquinariaAPIView(generics.DestroyAPIView):
#     queryset = models.MiModelo.objects.all()
