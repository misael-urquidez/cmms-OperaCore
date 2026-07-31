from datetime import date, datetime, time, timedelta

from django.db.models import F
from django.db.utils import ProgrammingError
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.fallas.models import ReporteFalla
from apps.inventario.models import Refaccion
from apps.mantenimiento.models import OrdenMantenimiento
from apps.maquinaria.models import Maquina


NO_VIVOS_ORDEN = ["CERRA", "CANCE"]
ESTADOS_VIVOS_REPORTE = ["ABIER", "ENATE", "ENESP"]


class NotificacionesListAPIView(APIView):
    def get(self, request):
        hoy = date.today()
        dentro_de_7 = hoy + timedelta(days=7)

        trabajador_id = request.query_params.get("trabajador")
        rol = request.query_params.get("rol")
        es_tecnico = rol == "TECNI"

        notificaciones = []

        # 1. Próximos preventivos (PREVE con fechaprogramada entre hoy y hoy+7)
        qs_preve = OrdenMantenimiento.objects.filter(
            tipo_mantenimiento_id="PREVE",
            fechaprogramada__gte=hoy,
            fechaprogramada__lte=dentro_de_7,
        ).exclude(estado_orden_id__in=NO_VIVOS_ORDEN).select_related("maquina")
        if es_tecnico and trabajador_id:
            qs_preve = qs_preve.filter(trabajador_id=trabajador_id)
        for o in qs_preve:
            notificaciones.append({
                "id": f"preve_{o.folio}",
                "tipo": "PREVE_PROXIMO",
                "mensaje": f"Mantenimiento preventivo de {o.maquina.nombre if o.maquina else '—'}",
                "detalle": f"Programado para {o.fechaprogramada.strftime('%d/%m/%Y')}",
                "url": "/mantenimiento/",
                "gravedad": "info",
                "fecha": o.fechaprogramada.isoformat(),
            })

        # 2. Órdenes atrasadas (fechaprogramada < hoy, no cerradas/canceladas)
        qs_retraso = OrdenMantenimiento.objects.filter(
            fechaprogramada__isnull=False,
            fechaprogramada__lt=hoy,
        ).exclude(estado_orden_id__in=NO_VIVOS_ORDEN).select_related("maquina")
        if es_tecnico and trabajador_id:
            qs_retraso = qs_retraso.filter(trabajador_id=trabajador_id)
        for o in qs_retraso:
            notificaciones.append({
                "id": f"retraso_{o.folio}",
                "tipo": "RETRASO_ORDEN",
                "mensaje": f"Orden {o.folio} — {o.maquina.nombre if o.maquina else '—'}",
                "detalle": f"Programada para {o.fechaprogramada.strftime('%d/%m/%Y')} (atrasada)",
                "url": "/mantenimiento/",
                "gravedad": "warning",
                "fecha": o.fechaprogramada.isoformat(),
            })

        # 3. Stock bajo (stock <= stockminimo)
        qs_stock = Refaccion.objects.filter(stock__lte=F("stockminimo")).select_related("proveedor")
        for r in qs_stock:
            notificaciones.append({
                "id": f"stock_{r.numeroregistro}",
                "tipo": "STOCK_BAJO",
                "mensaje": f"Stock bajo: {r.nombre}",
                "detalle": f"{r.stock} uds (mínimo {r.stockminimo})",
                "url": "/inventario/refacciones/",
                "gravedad": "warning",
                "fecha": hoy.isoformat(),
            })

        # 4. Punto de reorden (puntoreorden no nulo y stock <= puntoreorden)
        qs_reorden = Refaccion.objects.filter(
            puntoreorden__isnull=False,
            stock__lte=F("puntoreorden"),
        ).select_related("proveedor")
        for r in qs_reorden:
            notificaciones.append({
                "id": f"reorden_{r.numeroregistro}",
                "tipo": "PUNTO_REORDEN",
                "mensaje": f"Punto de reorden: {r.nombre}",
                "detalle": f"{r.stock} uds (reorden en {r.puntoreorden})",
                "url": "/inventario/refacciones/",
                "gravedad": "danger",
                "fecha": hoy.isoformat(),
            })

        # 5. Reportes de falla con severidad urgente (CRITI o ALTA) abiertos
        qs_urgentes = ReporteFalla.objects.filter(
            tipo_severidad_id__in=["CRITI", "ALTA"],
            estado_reporte_id__in=ESTADOS_VIVOS_REPORTE,
        ).select_related("maquina", "trabajador")
        for rf in qs_urgentes:
            notificaciones.append({
                "id": f"urgente_{rf.numeroRegistro}",
                "tipo": "REPORTE_URGENTE",
                "mensaje": f"Reporte {rf.tipo_severidad_id}: {rf.asunto}",
                "detalle": f"Máquina {rf.maquina.nombre if rf.maquina else '—'}",
                "url": "/fallas/",
                "gravedad": "danger",
                "fecha": rf.fechaCreacion.isoformat(),
            })

        # 6. Órdenes sin asignar (SOLIC con más de 1 día)
        qs_sin_asignar = OrdenMantenimiento.objects.filter(
            estado_orden_id="SOLIC",
            fechacreacion__lt=hoy - timedelta(days=1),
        ).select_related("maquina")
        for o in qs_sin_asignar:
            notificaciones.append({
                "id": f"sin_asignar_{o.folio}",
                "tipo": "SIN_ASIGNAR",
                "mensaje": f"Orden sin asignar: {o.folio}",
                "detalle": f"Máquina {o.maquina.nombre if o.maquina else '—'}",
                "url": "/mantenimiento/",
                "gravedad": "warning",
                "fecha": o.fechacreacion.isoformat(),
            })

        # 7. Máquinas caídas (FALLO/MANTE) por más de 24h
        try:
            from apps.maquinaria.models import HistorialEstadoMaquina
            hace_24h = timezone.make_aware(datetime.combine(hoy - timedelta(days=1), time.min))
            maquinas_caidas = Maquina.objects.filter(estado_maquina__in=["FALLO", "MANTE"])
            for m in maquinas_caidas:
                ultimo = HistorialEstadoMaquina.objects.filter(
                    maquina=m,
                    estado_nuevo_id=m.estado_maquina,
                ).order_by("-fecha").first()
                if ultimo and ultimo.fecha < hace_24h:
                    notificaciones.append({
                        "id": f"maquina_caida_{m.codigo}",
                        "tipo": "MAQUINA_CAIDA",
                        "mensaje": f"Máquina {m.nombre} en estado {m.estado_maquina}",
                        "detalle": f"Desde {ultimo.fecha.strftime('%d/%m/%Y %H:%M')}",
                        "url": "/maquinaria/",
                        "gravedad": "danger",
                        "fecha": ultimo.fecha.date().isoformat(),
                    })
        except ProgrammingError:
            pass

        notificaciones.sort(key=lambda n: n["fecha"], reverse=True)

        return Response(notificaciones, status=status.HTTP_200_OK)