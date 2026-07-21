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

    queryset = (
        models.ReporteFalla.objects
        .select_related("maquina", "trabajador", "tipo_falla", "tipo_severidad")
        .order_by("-fechaCreacion", "-horaCreacion")
    )
    serializer_class = serializers.ReporteFallaListSerializer


class ReporteFallaDetailAPIView(generics.RetrieveAPIView):

    queryset = models.ReporteFalla.objects.select_related(
        "maquina", "trabajador", "tipo_falla", "tipo_severidad"
    )
    serializer_class = serializers.ReporteFallaDetailSerializer


class ReporteFallaCreateAPIView(generics.CreateAPIView):

    serializer_class = serializers.ReporteFallaCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reporte = serializer.save()
        data = serializers.ReporteFallaDetailSerializer(reporte).data
        return Response(data, status=status.HTTP_201_CREATED)
    
class CatalogosReporteAPIView(APIView):
    """Junta los 4 catalogos que usa el formulario de 'Reportar Falla' en
    una sola respuesta, para que el client no tenga que hacer 4 llamadas
    HTTP separadas y secuenciales cada vez que carga la pagina."""

    def get(self, request):
        data = {
            "severidades": serializers.TipoSeveridadSerializer(
                models.TipoSeveridad.objects.all(), many=True
            ).data,
            "tipos_falla": serializers.TipoFallaSerializer(
                models.TipoFalla.objects.all(), many=True
            ).data,
            "maquinas": serializers.MaquinaSerializer(
                models.Maquina.objects.all(), many=True
            ).data,
            "estados": serializers.EstadoReporteSerializer(
                models.EstadoReporte.objects.all(), many=True
            ).data,
        }
        return Response(data, status=status.HTTP_200_OK)
