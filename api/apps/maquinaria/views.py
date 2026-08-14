from django.core.exceptions import ValidationError
from django.db import connection
from django.db.utils import OperationalError
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import models
from .models import Maquina
from .serializers import *
from .services import cambiar_estado_maquina


class PingAPIView(APIView):
    """Endpoint de prueba: confirma que el módulo Maquinaria responde."""

    def get(self, request):
        return Response({"modulo": "maquinaria", "status": "ok"}, status=status.HTTP_200_OK)


# ==========================================================
# PLANTA
# ==========================================================
class ListarPlantaAPIView(generics.ListAPIView):
    queryset = models.Planta.objects.all()
    serializer_class = ListPlantaSerializer

class DetailPlantaAPIView(generics.RetrieveAPIView):
    queryset = models.Planta.objects.all()
    serializer_class = DetailPlantaSerializer
    lookup_field = 'codigo'

class CrearPlantaAPIView(generics.CreateAPIView):
    queryset = models.Planta.objects.all()
    serializer_class = CreatePlantaSerializer

class UpdatePlantaAPIView(generics.UpdateAPIView):
    queryset = models.Planta.objects.all()
    serializer_class = UpdatePlantaSerializer
    lookup_field = 'codigo'


# ==========================================================
# AREA
# ==========================================================
class ListarAreaAPIView(generics.ListAPIView):
    queryset = models.Area.objects.all()
    serializer_class = ListAreaSerializer

class DetailAreaAPIView(generics.RetrieveAPIView):
    queryset = models.Area.objects.all()
    serializer_class = DetailAreaSerializer
    lookup_field = 'codigo'

class CrearAreaAPIView(generics.CreateAPIView):
    queryset = models.Area.objects.all()
    serializer_class = CreateAreaSerializer

class UpdateAreaAPIView(generics.UpdateAPIView):
    queryset = models.Area.objects.all()
    serializer_class = UpdateAreaSerializer
    lookup_field = 'codigo'


# ==========================================================
# EDO MAQUINA
# ==========================================================
class ListarEdoMaquinaAPIView(generics.ListAPIView):
    queryset = models.EdoMaquina.objects.all()
    serializer_class = ListEdoMaquinaSerializer

class DetailEdoMaquinaAPIView(generics.RetrieveAPIView):
    queryset = models.EdoMaquina.objects.all()
    serializer_class = DetailEdoMaquinaSerializer
    lookup_field = 'codigo'

class CrearEdoMaquinaAPIView(generics.CreateAPIView):
    queryset = models.EdoMaquina.objects.all()
    serializer_class = CreateEdoMaquinaSerializer

class UpdateEdoMaquinaAPIView(generics.UpdateAPIView):
    queryset = models.EdoMaquina.objects.all()
    serializer_class = UpdateEdoMaquinaSerializer
    lookup_field = 'codigo'


# ==========================================================
# LINEA
# ==========================================================
class ListarLineaAPIView(generics.ListAPIView):
    queryset = models.Linea.objects.all()
    serializer_class = ListLineaSerializer

class DetailLineaAPIView(generics.RetrieveAPIView):
    queryset = models.Linea.objects.all()
    serializer_class = DetailLineaSerializer
    lookup_field = 'codigo'

class CrearLineaAPIView(generics.CreateAPIView):
    queryset = models.Linea.objects.all()
    serializer_class = CreateLineaSerializer

class UpdateLineaAPIView(generics.UpdateAPIView):
    queryset = models.Linea.objects.all()
    serializer_class = UpdateLineaSerializer
    lookup_field = 'codigo'


# ==========================================================
# MARCA
# ==========================================================
class ListarMarcaAPIView(generics.ListAPIView):
    queryset = models.Marca.objects.all()
    serializer_class = ListMarcaSerializer

class DetailMarcaAPIView(generics.RetrieveAPIView):
    queryset = models.Marca.objects.all()
    serializer_class = DetailMarcaSerializer
    lookup_field = 'clave'

class CrearMarcaAPIView(generics.CreateAPIView):
    queryset = models.Marca.objects.all()
    serializer_class = CreateMarcaSerializer

class UpdateMarcaAPIView(generics.UpdateAPIView):
    queryset = models.Marca.objects.all()
    serializer_class = UpdateMarcaSerializer
    lookup_field = 'clave'


# ==========================================================
# MODELO
# ==========================================================
class ListarModeloAPIView(generics.ListAPIView):
    queryset = models.Modelo.objects.all()
    serializer_class = ListModeloSerializer

class DetailModeloAPIView(generics.RetrieveAPIView):
    queryset = models.Modelo.objects.all()
    serializer_class = DetailModeloSerializer
    lookup_field = 'codigo'

class CrearModeloAPIView(generics.CreateAPIView):
    queryset = models.Modelo.objects.all()
    serializer_class = CreateModeloSerializer

class UpdateModeloAPIView(generics.UpdateAPIView):
    queryset = models.Modelo.objects.all()
    serializer_class = UpdateModeloSerializer
    lookup_field = 'codigo'


# ==========================================================
# TIPO MAQUINA
# ==========================================================
class ListarTipoMaquinaAPIView(generics.ListAPIView):
    queryset = models.TipoMaquina.objects.all()
    serializer_class = ListTipoMaquinaSerializer

class DetailTipoMaquinaAPIView(generics.RetrieveAPIView):
    queryset = models.TipoMaquina.objects.all()
    serializer_class = DetailTipoMaquinaSerializer

class CrearTipoMaquinaAPIView(generics.CreateAPIView):
    queryset = models.TipoMaquina.objects.all()
    serializer_class = CreateTipoMaquinaSerializer

class UpdateTipoMaquinaAPIView(generics.UpdateAPIView):
    queryset = models.TipoMaquina.objects.all()
    serializer_class = UpdateTipoMaquinaSerializer


# ==========================================================
# MAQUINA
# ==========================================================
class ListarMaquinaAPIView(generics.ListAPIView):
    """Retorna un listado JSON de todas las máquinas usando ListMaquinaSerializer."""
    queryset = Maquina.objects.all()
    serializer_class = ListMaquinaSerializer

class DetailMaquinaAPIView(generics.RetrieveAPIView):
    """Retorna el detalle completo en JSON de una máquina por su código."""
    queryset = Maquina.objects.all()
    serializer_class = DetailMaquinaSerializer
    lookup_field = 'codigo'

class CrearMaquinaAPIView(generics.CreateAPIView):
    """Permite registrar una nueva máquina mediante la API REST."""
    queryset = Maquina.objects.all()
    serializer_class = CreateMaquinaSerializer

class UpdateMaquinaAPIView(generics.UpdateAPIView):
    """Permite actualizar la información de una máquina existente."""
    queryset = Maquina.objects.all()
    serializer_class = UpdateMaquinaSerializer
    lookup_field = 'codigo'


# ==========================================================
# CAMBIOS DE ESTADO MANUALES (nuevo)
# ==========================================================
class ValidarMaquinaAPIView(APIView):
    """ESPER -> OPERA. El admin/encargado valida que la reparación quedó bien."""
    def patch(self, request, codigo):
        try:
            maquina = cambiar_estado_maquina(codigo, "OPERA", "manual", None)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=400)
        return Response({"codigo": maquina.codigo, "estado_maquina": maquina.estado_maquina_id})


class DeshabilitarMaquinaAPIView(APIView):
    """OPERA/FALLO/MANTE/ESPER -> DESHA. Se puede dar de baja desde
    cualquier estado del ciclo de vida de la máquina, excepto si ya
    está deshabilitada (para no dejarlo pasar como no-op silencioso)."""
    def patch(self, request, codigo):
        maquina = get_object_or_404(Maquina, codigo=codigo)
        if maquina.estado_maquina_id == "DESHA":
            return Response(
                {"detail": "La máquina ya se encuentra deshabilitada."},
                status=400,
            )
        try:
            maquina = cambiar_estado_maquina(codigo, "DESHA", "manual", None)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=400)
        return Response({"codigo": maquina.codigo, "estado_maquina": maquina.estado_maquina_id})


class ReactivarMaquinaAPIView(APIView):
    """DESHA -> OPERA."""
    def patch(self, request, codigo):
        try:
            maquina = cambiar_estado_maquina(codigo, "OPERA", "manual", None)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=400)
        return Response({"codigo": maquina.codigo, "estado_maquina": maquina.estado_maquina_id})


def _filas_a_dicts(cur):
    columnas = [c[0] for c in cur.description]
    data = [dict(zip(columnas, fila)) for fila in cur.fetchall()]
    for row in data:
        for k, v in row.items():
            if hasattr(v, "isoformat"):  # date/datetime -> string
                row[k] = v.isoformat()
    return data


class ResumenMaquinaAPIView(APIView):
    """Ficha resumen de una maquina (nombre, estado, total de fallas,
    total de ordenes de mantenimiento, horas de operacion acumuladas,
    e indicadores vigentes: mtbf, mttr, % disponibilidad) via
    sp_resumen_maquina.
    GET /maquinaria/v1/maquina/<str:codigo>/resumen/"""

    def get(self, request, codigo):
        try:
            with connection.cursor() as cur:
                cur.callproc("sp_resumen_maquina", [codigo, "", "", 0, 0, 0, 0, 0, 0, 0, 0])
                cur.execute(
                    "SELECT @_sp_resumen_maquina_1, @_sp_resumen_maquina_2, "
                    "@_sp_resumen_maquina_3, @_sp_resumen_maquina_4, "
                    "@_sp_resumen_maquina_5, @_sp_resumen_maquina_6, "
                    "@_sp_resumen_maquina_7, @_sp_resumen_maquina_8, "
                    "@_sp_resumen_maquina_9, @_sp_resumen_maquina_10"
                )
                (
                    nombre, estado, total_fallas, total_ordenes,
                    horas_operacion, mtbf, mttr, disponibilidad,
                    tiempo_inactividad, numero_reparaciones,
                ) = cur.fetchone()
        except OperationalError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if nombre is None:
            return Response(
                {"detail": "La maquina especificada no existe."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "maquina": codigo,
                "nombre": nombre,
                "estado": estado,
                "total_fallas": total_fallas,
                "total_ordenes": total_ordenes,
                "horas_operacion": horas_operacion,
                "mtbf": mtbf,
                "mttr": mttr,
                "disponibilidad": disponibilidad,
                "tiempo_inactividad": tiempo_inactividad,
                "numero_reparaciones": numero_reparaciones,
            },
            status=status.HTTP_200_OK,
        )


class HistorialMaquinaAPIView(APIView):
    """Historial combinado (ordenes de mantenimiento + reportes de falla)
    de una maquina, con el trabajador que atendio cada una, via
    sp_historial_maquina.
    GET /maquinaria/v1/maquina/<str:codigo>/historial/"""

    def get(self, request, codigo):
        try:
            with connection.cursor() as cur:
                cur.callproc("sp_historial_maquina", [codigo])
                data = _filas_a_dicts(cur)
        except OperationalError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"maquina": codigo, "historial": data}, status=status.HTTP_200_OK)