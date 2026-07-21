from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import models, serializers


class PingAPIView(APIView):

    def get(self, request):
        return Response({"modulo": "fallas", "status": "ok"}, status=status.HTTP_200_OK)

#------------TIPO FALLA ----------------------------------------------------
class ListarTipoFallaAPIView(generics.ListAPIView):
    queryset = models.TipoFalla.objects.all()
    serializer_class = serializers.ListTipoFallaSerializer

<<<<<<< HEAD
class DetailTipoFallaAPIView(generics.RetrieveAPIView):
    queryset = models.TipoFalla.objects.all()
    serializer_class = serializers.DetailTipoFallaSerializer

class CrearTipoFallaAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateTipoFallaSerializer

class UpdateTipoFallaAPIView(generics.UpdateAPIView):
    queryset = models.TipoFalla.objects.all()
    serializer_class = serializers.UpdateTipoFallaSerializer

#------------TIPO SEVERIDAD ----------------------------------------------------
class ListarTipoSeveridadAPIView(generics.ListAPIView):
    queryset = models.TipoSeveridad.objects.all()
    serializer_class = serializers.ListTipoSeveridadSerializer

class DetailTipoSeveridadAPIView(generics.RetrieveAPIView):
    queryset = models.TipoSeveridad.objects.all()
    serializer_class = serializers.DetailTipoSeveridadSerializer
    lookup_field = 'codigo'

class CrearTipoSeveridadAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateTipoSeveridadSerializer

class UpdateTipoSeveridadAPIView(generics.UpdateAPIView):
    queryset = models.TipoSeveridad.objects.all()
    serializer_class = serializers.UpdateTipoSeveridadSerializer
    lookup_field = 'codigo'

#------------EDO REPORTE ----------------------------------------------------
class ListarEdoReporteAPIView(generics.ListAPIView):
    queryset = models.EdoReporte.objects.all()
    serializer_class = serializers.ListEdoReporteSerializer

class DetailEdoReporteAPIView(generics.RetrieveAPIView):
    queryset = models.EdoReporte.objects.all()
    serializer_class = serializers.DetailEdoReporteSerializer
    lookup_field = 'codigo'

class CrearEdoReporteAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateEdoReporteSerializer

class UpdateEdoReporteAPIView(generics.UpdateAPIView):
    queryset = models.EdoReporte.objects.all()
    serializer_class = serializers.UpdateEdoReporteSerializer
    lookup_field = 'codigo'

#------------TIPO REPORTE ----------------------------------------------------
class ListarTipoReporteAPIView(generics.ListAPIView):
    queryset = models.TipoReporte.objects.all()
    serializer_class = serializers.ListTipoReporteSerializer

class DetailTipoReporteAPIView(generics.RetrieveAPIView):
    queryset = models.TipoReporte.objects.all()
    serializer_class = serializers.DetailTipoReporteSerializer
    lookup_field = 'tipo_falla' 

class CrearTipoReporteAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateTipoReporteSerializer

class UpdateTipoReporteAPIView(generics.UpdateAPIView):
    queryset = models.TipoReporte.objects.all()
    serializer_class = serializers.UpdateTipoReporteSerializer
    lookup_field = 'tipo_falla' 

#------------REPORTE FALLA ----------------------------------------------------
class ListarReporteFallaAPIView(generics.ListAPIView):
    queryset = models.ReporteFalla.objects.all()
    serializer_class = serializers.ListReporteFallaSerializer

class DetailReporteFallaAPIView(generics.RetrieveAPIView):
    queryset = models.ReporteFalla.objects.all()
    serializer_class = serializers.DetailReporteFallaSerializer

class CrearReporteFallaAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateReporteFallaSerializer

class UpdateReporteFallaAPIView(generics.UpdateAPIView):
    queryset = models.ReporteFalla.objects.all()
    serializer_class = serializers.UpdateReporteFallaSerializer
=======
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
>>>>>>> origin/main
