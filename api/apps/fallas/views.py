from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from . import models
from . import serializers


class PingAPIView(APIView):
    """Endpoint de prueba: confirma que el modulo Fallas responde."""

    def get(self, request):
        return Response({"modulo": "fallas", "status": "ok"}, status=status.HTTP_200_OK)

#------------TIPO FALLA ----------------------------------------------------
class ListarTipoFallaAPIView(generics.ListAPIView):
    queryset = models.TipoFalla.objects.all()
    serializer_class = serializers.ListTipoFallaSerializer

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
