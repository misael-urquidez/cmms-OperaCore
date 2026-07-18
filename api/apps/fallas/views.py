from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import models, serializers


class PingAPIView(APIView):

    def get(self, request):
        return Response({"modulo": "fallas", "status": "ok"}, status=status.HTTP_200_OK)

#------------TIPO FALLA ----------------------------------------------------
class ListarReportesFallasAPIView(generics.ListAPIView):
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

#------------TIPO SEVERIDAD ----------------------------------------------------
class ListarTipoSeveridadAPIView(generics.ListAPIView):
    queryset = models.TipoSeveridad.objects.all()
    serializer_class = serializers.ListTipoSeveridadSerializer

class DetailTipoSeveridadAPIView(generics.RetrieveAPIView):
    queryset = models.TipoSeveridad.objects.all()
    serializer_class = serializers.DetailTipoSeveridadSerializer

class CrearTipoSeveridadAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateTipoSeveridadSerializer

class UpdateTipoSeveridadAPIView(generics.UpdateAPIView):
    queryset = models.TipoSeveridad.objects.all()
    serializer_class = serializers.UpdateTipoSeveridadSerializer

#------------EDO REPORTE ----------------------------------------------------
class ListarEdoReporteAPIView(generics.ListAPIView):
    queryset = models.EdoReporte.objects.all()
    serializer_class = serializers.ListEdoReporteSerializer

class DetailEdoReporteAPIView(generics.RetrieveAPIView):
    queryset = models.EdoReporte.objects.all()
    serializer_class = serializers.DetailEdoReporteSerializer

class CrearEdoReporteAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateEdoReporteSerializer

class UpdateEdoReporteAPIView(generics.UpdateAPIView):
    queryset = models.EdoReporte.objects.all()
    serializer_class = serializers.UpdateEdoReporteSerializer

#------------TIPO REPORTE ----------------------------------------------------
class ListarTipoReporteAPIView(generics.ListAPIView):
    queryset = models.TipoReporte.objects.all()
    serializer_class = serializers.ListTipoReporteSerializer

class DetailTipoReporteAPIView(generics.RetrieveAPIView):
    queryset = models.TipoReporte.objects.all()
    serializer_class = serializers.DetailTipoReporteSerializer

class CrearTipoReporteAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateTipoReporteSerializer

class UpdateTipoReporteAPIView(generics.UpdateAPIView):
    queryset = models.TipoReporte.objects.all()
    serializer_class = serializers.UpdateTipoReporteSerializer

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
