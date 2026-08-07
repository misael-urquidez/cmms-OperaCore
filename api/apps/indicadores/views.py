from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from django.db.models import F
from apps.monitoreo.models import Indicador
from apps.mantenimiento.models import OrdenMantenimiento
from apps.inventario.models import Refaccion
from . import models
from . import serializers


class PingAPIView(APIView):
    """Endpoint de prueba: confirma que el modulo Indicadores responde."""

    def get(self, request):
        return Response({"modulo": "indicadores", "status": "ok"}, status=status.HTTP_200_OK)


class ResumenIndicadoresAPIView(APIView):
    """Resumen para el Dashboard (RF-26): MTBF, MTTR y disponibilidad
    promedio de la flota (tomando el ultimo registro de INDICADOR por
    maquina), ordenes pendientes y alertas de inventario (refacciones
    en o debajo de su stock minimo)."""

    def get(self, request):
        # MySQL no soporta distinct("campo") como Postgres, asi que se
        # resuelve a mano: nos quedamos con el INDICADOR mas reciente
        # (numeroRegistro mayor) de cada maquina.
        ultimo_por_maquina = {}
        for ind in Indicador.objects.select_related("maquina").order_by("maquina", "-numeroRegistro"):
            if ind.maquina_id not in ultimo_por_maquina:
                ultimo_por_maquina[ind.maquina_id] = ind

        indicadores = list(ultimo_por_maquina.values())

        def promedio(campo):
            valores = [getattr(i, campo) for i in indicadores if getattr(i, campo) is not None]
            return round(sum(valores) / len(valores), 1) if valores else None

        # Detalle por maquina para la tablita del dashboard.
        por_maquina = []
        for ind in sorted(indicadores, key=lambda i: i.maquina_id or ""):
            nombre_maquina = ind.maquina.nombre if ind.maquina else ind.maquina_id
            por_maquina.append({
                "codigo": ind.maquina_id,
                "nombre": nombre_maquina,
                "mtbf": ind.mtbf,
                "mttr": ind.mttr,
                "disponibilidad": ind.porcentajeDispo,
            })

        data = {
            "mtbf_promedio": promedio("mtbf"),
            "mttr_promedio": promedio("mttr"),
            "disponibilidad_promedio": promedio("porcentajeDispo"),
            "maquinas_con_indicador": len(indicadores),
            "por_maquina": por_maquina,
            "ordenes_pendientes": OrdenMantenimiento.objects.filter(
                estado_orden_id="PENDI"
            ).count(),
            "alertas_inventario": Refaccion.objects.filter(
                stock__lte=F("stockminimo")
            ).count(),
        }
        return Response(data, status=status.HTTP_200_OK)


# A partir de aqui sigue el patron de tu maestro cuando agregues modelos reales:
#
# class ListIndicadoresAPIView(generics.ListAPIView):
#     queryset = models.MiModelo.objects.all()
#     serializer_class = serializers.ListMaquinaSerializer
#
# class DetailIndicadoresAPIView(generics.RetrieveAPIView):
#     queryset = models.MiModelo.objects.all()
#     serializer_class = serializers.DetailMaquinaSerializer
#
# class CreateIndicadoresAPIView(generics.CreateAPIView):
#     serializer_class = serializers.CreateMaquinaSerializer
#
# class UpdateIndicadoresAPIView(generics.UpdateAPIView):
#     queryset = models.MiModelo.objects.all()
#     serializer_class = serializers.CreateMaquinaSerializer
#
# class DeleteIndicadoresAPIView(generics.DestroyAPIView):
#     queryset = models.MiModelo.objects.all()