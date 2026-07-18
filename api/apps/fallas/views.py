from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import models, serializers


class PingAPIView(APIView):

    def get(self, request):
        return Response({"modulo": "fallas", "status": "ok"}, status=status.HTTP_200_OK)


class TipoSeveridadListAPIView(generics.ListAPIView):

    queryset = models.TipoSeveridad.objects.all()
    serializer_class = serializers.TipoSeveridadSerializer


class TipoFallaListAPIView(generics.ListAPIView):

    queryset = models.TipoFalla.objects.all()
    serializer_class = serializers.TipoFallaSerializer


class MaquinaListAPIView(generics.ListAPIView):

    queryset = models.Maquina.objects.all()
    serializer_class = serializers.MaquinaSerializer


class EstadoReporteListAPIView(generics.ListAPIView):

    queryset = models.EstadoReporte.objects.all()
    serializer_class = serializers.EstadoReporteSerializer


class ReporteFallaListAPIView(generics.ListAPIView):


    queryset = models.ReporteFalla.objects.all().order_by("-fechaCreacion", "-horaCreacion")
    serializer_class = serializers.ReporteFallaListSerializer


class ReporteFallaDetailAPIView(generics.RetrieveAPIView):


    queryset = models.ReporteFalla.objects.all()
    serializer_class = serializers.ReporteFallaDetailSerializer


class ReporteFallaCreateAPIView(generics.CreateAPIView):

    serializer_class = serializers.ReporteFallaCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reporte = serializer.save()
        data = serializers.ReporteFallaDetailSerializer(reporte).data
        return Response(data, status=status.HTTP_201_CREATED)
