from django.db.models import Prefetch
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView

from apps.fallas.models import (
    EstadoMaquina, EstadoReporte, Linea, Maquina, Marca, Modelo,
    ReporteFalla, TipoFalla, TipoMaquina, TipoSeveridad,
)
from apps.usuarios.models import Trabajador

from .models import Indicador, LecturaSensor
from .serializers import CrearMaquinaSerializer, LecturaSensorSerializer, ReporteFallaManualSerializer


class LecturaCreateAPIView(APIView):
    def post(self, request):
        serializer = LecturaSensorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lectura = serializer.save()
        data = LecturaSensorSerializer(lectura).data
        reporte = serializer.context.get("reporte_automatico")
        data["reporte_automatico"] = reporte.numeroRegistro if reporte else None
        data["requiere_revision_preventiva"] = serializer.context["requiere_revision"]
        return Response(data, status=status.HTTP_201_CREATED)


class MaquinaListAPIView(APIView):
    def get(self, request):
        # Una consulta de máquinas y una de lecturas recientes; evita N+1.
        maquinas = Maquina.objects.select_related("linea").prefetch_related(
            Prefetch("lecturasensor_set", queryset=LecturaSensor.objects.order_by("-timestamp"), to_attr="lecturas_recientes")
        ).order_by("linea__nombre", "nombre")
        data = []
        for maquina in maquinas:
            ultima = maquina.lecturas_recientes[0] if maquina.lecturas_recientes else None
            data.append({
                "codigo": maquina.codigo, "nombre": maquina.nombre,
                "linea": maquina.linea.nombre if maquina.linea else None,
                "linea_codigo": maquina.linea_id,
                "estado_maquina": maquina.estado_maquina, "modo_monitoreo": maquina.modo_monitoreo,
                "umbral_vibracion": maquina.umbral_vibracion,
                "requiere_revision_preventiva": maquina.requiere_revision_preventiva,
                "ultima_lectura": LecturaSensorSerializer(ultima).data if ultima else None,
            })
        return Response(data)


class IndicadoresMaquinaAPIView(APIView):
    def get(self, request, codigo):
        indicador = Indicador.objects.filter(maquina_id=codigo).order_by("-fechaInicio", "-numeroRegistro").first()
        if not indicador:
            return Response({"mtbf": None, "mttr": None, "disponibilidad": None})
        return Response({"mtbf": indicador.mtbf, "mttr": indicador.mttr, "disponibilidad": indicador.porcentajeDispo})


class HistorialLecturasAPIView(APIView):
    """Últimas N lecturas de una máquina, en orden cronológico (más viejo
    primero), para dibujar la tendencia de vibración en el panel lateral."""

    def get(self, request, codigo):
        try:
            maquina = Maquina.objects.get(codigo=codigo)
        except Maquina.DoesNotExist as exc:
            raise NotFound("Máquina no encontrada.") from exc
        try:
            limite = int(request.query_params.get("limite", 20))
        except ValueError:
            limite = 20
        limite = max(1, min(limite, 100))
        lecturas = LecturaSensor.objects.filter(maquina=maquina).order_by("-timestamp")[:limite]
        datos = LecturaSensorSerializer(lecturas, many=True).data
        return Response({"umbral_vibracion": maquina.umbral_vibracion, "lecturas": list(reversed(datos))})


class CatalogosMaquinaAPIView(APIView):
    """Catálogos para poblar los selects del formulario 'nueva máquina'."""

    def get(self, request):
        return Response({
            "lineas": list(Linea.objects.order_by("nombre").values("codigo", "nombre")),
            "marcas": list(Marca.objects.order_by("nombre").values("clave", "nombre")),
            "modelos": list(Modelo.objects.order_by("nombre").values("codigo", "nombre", "marca")),
            "tipos_maquina": list(TipoMaquina.objects.order_by("nombre").values("numeroRegistro", "nombre")),
            "estados_maquina": list(EstadoMaquina.objects.order_by("nombre").values("codigo", "nombre")),
            "modos_monitoreo": [{"valor": valor, "etiqueta": etiqueta} for valor, etiqueta in LecturaSensor.ORIGENES],
        })


class CrearMaquinaAPIView(APIView):
    def post(self, request):
        serializer = CrearMaquinaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        maquina = serializer.save()
        return Response({
            "codigo": maquina.codigo, "nombre": maquina.nombre,
            "linea": maquina.linea.nombre if maquina.linea else None,
            "linea_codigo": maquina.linea_id,
            "estado_maquina": maquina.estado_maquina, "modo_monitoreo": maquina.modo_monitoreo,
            "umbral_vibracion": maquina.umbral_vibracion,
            "requiere_revision_preventiva": maquina.requiere_revision_preventiva,
            "ultima_lectura": None,
        }, status=status.HTTP_201_CREATED)


class EstadoMaquinaAPIView(APIView):
    def get(self, request, codigo):
        try:
            maquina = Maquina.objects.get(codigo=codigo)
        except Maquina.DoesNotExist as exc:
            raise NotFound("Máquina no encontrada.") from exc
        falla = ReporteFalla.objects.filter(maquina=maquina).exclude(
            estado_reporte_id__in=["RESUE", "CERRA", "CANCE"]
        ).order_by("-fechaCreacion", "-horaCreacion").first()
        return Response({
            "falla_activa": bool(falla),
            "reporte_falla": falla.numeroRegistro if falla else None,
            "requiere_revision_preventiva": maquina.requiere_revision_preventiva,
        })


class ReportarFallaManualAPIView(APIView):
    def post(self, request):
        serializer = ReporteFallaManualSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = request.session.get("usuario")
        trabajador = Trabajador.objects.filter(numeroNomina=usuario.get("numeroNomina")).first() if usuario else None
        if not trabajador:
            return Response({"detail": "Se requiere una sesión de trabajador para reportar una falla."}, status=400)
        datos = serializer.validated_data
        reporte = ReporteFalla.objects.create(
            asunto=datos["asunto"], causaRaiz=datos["causaRaiz"], descripcion=datos.get("descripcion"),
            tiempoParo=datos.get("tiempoParo"), maquina=datos["maquina"], trabajador=trabajador,
            tipo_falla=TipoFalla.objects.get(numeroRegistro=datos["tipo_falla"]),
            tipo_severidad=TipoSeveridad.objects.get(codigo=datos["tipo_severidad"]),
            estado_reporte=EstadoReporte.objects.get(codigo="ABIER"),
            fechaCreacion=timezone.localdate(), horaCreacion=timezone.localtime().time(),
        )
        return Response({"numeroRegistro": reporte.numeroRegistro}, status=status.HTTP_201_CREATED)