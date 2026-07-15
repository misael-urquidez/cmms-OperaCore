from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from . import models
from . import serializers


class PingAPIView(APIView):
    """Endpoint de prueba: confirma que el modulo Inventario responde."""

    def get(self, request):
        return Response({"modulo": "inventario", "status": "ok"}, status=status.HTTP_200_OK)


# A partir de aqui sigue el patron de tu maestro cuando agregues modelos reales:
#
# class ListInventarioAPIView(generics.ListAPIView):
#     queryset = models.MiModelo.objects.all()
#     serializer_class = serializers.ListMaquinaSerializer
#
# class DetailInventarioAPIView(generics.RetrieveAPIView):
#     queryset = models.MiModelo.objects.all()
#     serializer_class = serializers.DetailMaquinaSerializer
#
# class CreateInventarioAPIView(generics.CreateAPIView):
#     serializer_class = serializers.CreateMaquinaSerializer
#
# class UpdateInventarioAPIView(generics.UpdateAPIView):
#     queryset = models.MiModelo.objects.all()
#     serializer_class = serializers.CreateMaquinaSerializer
#
# class DeleteInventarioAPIView(generics.DestroyAPIView):
#     queryset = models.MiModelo.objects.all()
