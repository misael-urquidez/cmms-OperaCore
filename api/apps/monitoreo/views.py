from django.core.exceptions import ValidationError
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

from . import services
from .models import Indicador, LecturaSensor, RegistroOps
from .serializers import (
    CrearMaquinaSerializer, LecturaSensorSerializer, ModoMonitoreoSerializer, ReparacionManualSerializer,
    RegistroOpsSerializer, ReporteFallaManualSerializer,
)


class LecturaCreateAPIView(APIView):
    def post(self, request):
        serializer = LecturaSensorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            lectura = serializer.save()
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
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
        from django.db.models import Count, Sum

        indicador = Indicador.objects.filter(maquina_id=codigo).order_by("-fechaInicio", "-numeroRegistro").first()

        fallas_qs = ReporteFalla.objects.filter(maquina_id=codigo)
        total_fallas = fallas_qs.count()
        total_tiempo_paro = fallas_qs.aggregate(total=Sum("tiempoParo"))["total"] or 0

        response = {
            "mtbf": indicador.mtbf if indicador else None,
            "mttr": indicador.mttr if indicador else None,
            "disponibilidad": indicador.porcentajeDispo if indicador else None,
            "numero_fallas": total_fallas,
            "tiempo_inactividad": total_tiempo_paro,
        }
        return Response(response)


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


class ModoMonitoreoAPIView(APIView):
    """Cambia el modo de monitoreo (manual/simulado/iot) de una máquina.

    Solo puede haber UNA máquina "vinculada" en modo iot a la vez -- hay un
    solo Wiimote físico, así que no tiene sentido que dos máquinas queden
    en iot simultáneamente (generaría ambigüedad sobre a cuál está atado
    el sensor). Al activar iot en una máquina, cualquier otra que ya
    estuviera en iot se libera automáticamente a modo manual."""

    def patch(self, request, codigo):
        try:
            maquina = Maquina.objects.get(codigo=codigo)
        except Maquina.DoesNotExist as exc:
            raise NotFound("Máquina no encontrada.") from exc
        serializer = ModoMonitoreoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        nuevo_modo = serializer.validated_data["modo_monitoreo"]

        maquina_liberada = None
        if nuevo_modo == LecturaSensor.ORIGEN_IOT:
            otra_en_iot = Maquina.objects.filter(
                modo_monitoreo=LecturaSensor.ORIGEN_IOT
            ).exclude(codigo=maquina.codigo).first()
            if otra_en_iot:
                otra_en_iot.modo_monitoreo = LecturaSensor.ORIGEN_MANUAL
                otra_en_iot.save(update_fields=["modo_monitoreo"])
                maquina_liberada = otra_en_iot.codigo

        maquina.modo_monitoreo = nuevo_modo
        maquina.save(update_fields=["modo_monitoreo"])
        return Response({
            "codigo": maquina.codigo,
            "modo_monitoreo": maquina.modo_monitoreo,
            "maquina_iot_liberada": maquina_liberada,
        })


class MaquinaIotActivaAPIView(APIView):
    """Devuelve el código de la única máquina que está en modo iot ahora
    mismo (o null si ninguna). Útil para que el script del Wiimote y el
    front confirmen a cuál máquina está vinculado el sensor sin tener que
    adivinar ni pasar el código a mano."""

    def get(self, request):
        maquina = Maquina.objects.filter(modo_monitoreo=LecturaSensor.ORIGEN_IOT).first()
        return Response({"codigo": maquina.codigo if maquina else None})


class SimularLecturaAPIView(APIView):
    """Genera una lectura simulada bajo demanda (botón 'Simular ahora').
    Requiere que la máquina esté en modo_monitoreo='simulado'."""

    def post(self, request, codigo):
        try:
            maquina = Maquina.objects.get(codigo=codigo)
        except Maquina.DoesNotExist as exc:
            raise NotFound("Máquina no encontrada.") from exc
        if maquina.modo_monitoreo != LecturaSensor.ORIGEN_SIMULADO:
            return Response(
                {"detail": "La máquina no está en modo simulado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        lectura, reporte, requiere_revision = services.generar_lectura_simulada(maquina)
        data = LecturaSensorSerializer(lectura).data
        data["reporte_automatico"] = reporte.numeroRegistro if reporte else None
        data["requiere_revision_preventiva"] = requiere_revision
        return Response(data, status=status.HTTP_201_CREATED)

class ReparacionManualAPIView(APIView):
    """Registra una reparación con tiempoParo fijo a mano (alimenta MTTR).
    No recibe ni escribe mttr -- eso lo calcula el trigger de MySQL en
    cuanto se cierra la orden que crea internamente."""

    def post(self, request, codigo):
        try:
            maquina = Maquina.objects.get(codigo=codigo)
        except Maquina.DoesNotExist as exc:
            raise NotFound("Máquina no encontrada.") from exc
        serializer = ReparacionManualSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            reporte = services.registrar_reparacion_manual(maquina=maquina, **serializer.validated_data)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "numeroRegistro": reporte.numeroRegistro,
            "maquina": maquina.codigo,
            "tiempoParo": reporte.tiempoParo,
        }, status=status.HTTP_201_CREATED)

class RegistroOpsAPIView(APIView):
    """Lista y crea periodos de horas de operación de una máquina.
    No recibe ni escribe mtbf/mttr/disponibilidad -- eso lo calculan
    los triggers de MySQL en cuanto se inserta el registro."""

    def get(self, request, codigo):
        try:
            maquina = Maquina.objects.get(codigo=codigo)
        except Maquina.DoesNotExist as exc:
            raise NotFound("Máquina no encontrada.") from exc
        registros = RegistroOps.objects.filter(maquina=maquina).order_by("-fechaInicio")
        return Response([
            {
                "numeroRegistro": r.numeroRegistro,
                "fechaInicio": r.fechaInicio.isoformat(),
                "fechaFin": r.fechaFin.isoformat(),
                "horasOperacion": r.horasOperacion,
                "maquina": r.maquina_id,
            }
            for r in registros
        ])

    def post(self, request, codigo):
        try:
            maquina = Maquina.objects.get(codigo=codigo)
        except Maquina.DoesNotExist as exc:
            raise NotFound("Máquina no encontrada.") from exc
        serializer = RegistroOpsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        registro = services.registrar_horas_operacion(maquina=maquina, **serializer.validated_data)
        return Response({
            "numeroRegistro": registro.numeroRegistro,
            "maquina": maquina.codigo,
            "horasOperacion": registro.horasOperacion,
        }, status=status.HTTP_201_CREATED)


class RegistroOpsUpdateAPIView(APIView):
    """Actualiza un periodo de horas de operación existente y
    recalcula el MTBF."""

    def patch(self, request, pk):
        try:
            registro = RegistroOps.objects.get(pk=pk)
        except RegistroOps.DoesNotExist as exc:
            raise NotFound("Registro no encontrado.") from exc
        serializer = RegistroOpsSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        for attr, val in serializer.validated_data.items():
            setattr(registro, attr, val)
        registro.save()
        services.recalcular_mtbf_maquina(registro.maquina_id)
        return Response({
            "numeroRegistro": registro.numeroRegistro,
            "maquina": registro.maquina_id,
            "horasOperacion": registro.horasOperacion,
        })


class RegistroOpsDeleteAPIView(APIView):
    """Elimina un periodo de horas de operación y recalcula el MTBF."""

    def delete(self, request, pk):
        try:
            registro = RegistroOps.objects.get(pk=pk)
        except RegistroOps.DoesNotExist as exc:
            raise NotFound("Registro no encontrado.") from exc
        maquina_codigo = registro.maquina_id
        registro.delete()
        services.recalcular_mtbf_maquina(maquina_codigo)
        return Response({"detail": "Registro eliminado."}, status=status.HTTP_200_OK)


class ReparacionIotAPIView(APIView):
    """Resuelve desde IoT la falla activa de una máquina."""

    def post(self, request, codigo):
        try:
            maquina = Maquina.objects.get(codigo=codigo)
        except Maquina.DoesNotExist as exc:
            raise NotFound("Máquina no encontrada.") from exc
        falla = services.reparar_via_iot(maquina)
        if falla is None:
            return Response({"resultado": "sin_falla", "maquina": maquina.codigo})
        return Response({
            "resultado": "reparado", "maquina": maquina.codigo,
            "reporte_falla": falla.numeroRegistro,
        })