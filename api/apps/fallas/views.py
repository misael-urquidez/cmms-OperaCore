import os

from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.usuarios.models import Trabajador
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
        .select_related("maquina", "trabajador", "tipo_severidad")
        .order_by("-fechaCreacion", "-horaCreacion")
    )
    serializer_class = serializers.ReporteFallaListSerializer

#cambio

class ReporteFallaDetailAPIView(generics.RetrieveAPIView):

    queryset = models.ReporteFalla.objects.select_related(
        "maquina", "trabajador", "tipo_severidad"
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


class ReporteFallaUpdateAPIView(generics.UpdateAPIView):

    queryset = models.ReporteFalla.objects.all()
    serializer_class = serializers.ReporteFallaUpdateSerializer

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        reporte = models.ReporteFalla.objects.get(pk=kwargs["pk"])

        tipo_falla_ids = request.data.getlist("tipo_falla_ids")
        if tipo_falla_ids:
            models.TipoReporte.objects.filter(reporte_falla=reporte).delete()
            for tf_id in tipo_falla_ids:
                models.TipoReporte.objects.create(
                    tipo_falla_id=int(tf_id),
                    reporte_falla=reporte,
                )

        imagen_file = request.FILES.get("imagen")
        if imagen_file:
            carpeta = os.path.join(settings.MEDIA_ROOT, "fallas")
            os.makedirs(carpeta, exist_ok=True)
            with open(os.path.join(carpeta, imagen_file.name), "wb+") as dest:
                for chunk in imagen_file.chunks():
                    dest.write(chunk)
            reporte.imagen = f"fallas/{imagen_file.name}"
            reporte.save(update_fields=["imagen"])

        return Response(
            serializers.ReporteFallaDetailSerializer(reporte).data,
            status=status.HTTP_200_OK,
        )
    
class TrabajadorListAPIView(generics.ListAPIView):
    """Listado ligero de trabajadores (solo nomina + nombre) para el
    select del formulario de reporte de falla."""

    queryset = Trabajador.objects.filter(actividad=True).order_by("nombre")
    serializer_class = serializers.TrabajadorLightSerializer


class CatalogosReporteAPIView(APIView):
    """Junta los catalogos que usa el formulario de 'Reportar Falla' en
    una sola respuesta, para que el client no tenga que hacer N llamadas
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
            "trabajadores": serializers.TrabajadorLightSerializer(
                Trabajador.objects.filter(actividad=True).order_by("nombre"),
                many=True,
            ).data,
        }
        return Response(data, status=status.HTTP_200_OK) 