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


class TipoFallaCreateAPIView(generics.CreateAPIView):

    serializer_class = serializers.TipoFallaCreateSerializer


class TipoSeveridadCreateAPIView(generics.CreateAPIView):

    serializer_class = serializers.TipoSeveridadCreateSerializer


class TipoSeveridadDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """GET trae un registro, PUT/PATCH lo edita, DELETE lo borra.
    Reutiliza el CreateSerializer para escritura porque tiene los mismos
    campos editables que el de detalle."""

    queryset = models.TipoSeveridad.objects.all()
    lookup_field = "codigo"

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return serializers.TipoSeveridadCreateSerializer
        return serializers.TipoSeveridadDetailSerializer


class TipoFallaDetailAPIView(generics.RetrieveUpdateDestroyAPIView):

    queryset = models.TipoFalla.objects.all()
    lookup_field = "numeroRegistro"

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return serializers.TipoFallaCreateSerializer
        return serializers.TipoFallaDetailSerializer


class MaquinaListAPIView(generics.ListAPIView):

    queryset = models.Maquina.objects.all()
    serializer_class = serializers.MaquinaSerializer


class EstadoReporteListAPIView(generics.ListAPIView):

    queryset = models.EstadoReporte.objects.all()
    serializer_class = serializers.EstadoReporteSerializer


class EstadoReporteCreateAPIView(generics.CreateAPIView):
    queryset = models.EstadoReporte.objects.all()
    serializer_class = serializers.EstadoReporteDetailSerializer


class EstadoReporteDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.EstadoReporte.objects.all()
    serializer_class = serializers.EstadoReporteDetailSerializer
    lookup_field = "codigo"


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


# ------------ TIPO_REPORTE (llave compuesta: tipo_falla, reporte_falla) --
# PK real en BD: (tipo_falla, reporte_falla). Detail resuelve su propio
# get_object a mano, igual que las tablas puente de inventario/mantenimiento.
class TipoReporteListAPIView(generics.ListAPIView):
    queryset = models.TipoReporte.objects.all()
    serializer_class = serializers.ListTipoReporteSerializer


class TipoReporteCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateTipoReporteSerializer


class TipoReporteDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.TipoReporte.objects.all()
    serializer_class = serializers.DetailTipoReporteSerializer

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return serializers.UpdateTipoReporteSerializer
        return serializers.DetailTipoReporteSerializer

    def get_object(self):
        obj = generics.get_object_or_404(
            self.get_queryset(),
            tipo_falla=self.kwargs["tipo_falla"],
            reporte_falla=self.kwargs["reporte_falla"],
        )
        self.check_object_permissions(self.request, obj)
        return obj
