from django.db import connection
from django.db.utils import OperationalError
from django.db.models import Case, ExpressionWrapper, F, FloatField, OuterRef, Subquery, Sum, Value, When
from django.db.models.functions import Coalesce, Least, Round
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from apps.mantenimiento.models import Movimiento
from apps.monitoreo.models import RegistroOps
from . import models
from . import serializers


# ------------ PING & CATÁLOGOS AGREGADOS ----------------------------------
class PingAPIView(APIView):
    """Endpoint de prueba: confirma que el módulo Inventario responde."""
    def get(self, request):
        return Response({"modulo": "inventario", "status": "ok"}, status=status.HTTP_200_OK)


class CatalogosInventarioAPIView(APIView):
    """Junta los catálogos principales para los formularios de registro."""
    def get(self, request):
        data = {
            "clasificaciones": serializers.ListClasificacionSerializer(
                models.Clasificacion.objects.all(), many=True
            ).data,
            "estados_herramienta": serializers.ListEdoHerramientaSerializer(
                models.EdoHerramienta.objects.all(), many=True
            ).data,
            "estados_pieza": serializers.ListEdoPiezaSerializer(
                models.EdoPieza.objects.all(), many=True
            ).data,
            "estados_refaccion": serializers.ListEdoRefaccionSerializer(
                models.EdoRefaccion.objects.all(), many=True
            ).data,
            "tipos_herramienta": serializers.ListTipoHerramientaSerializer(
                models.TipoHerramienta.objects.all(), many=True
            ).data,
            "tipos_pieza": serializers.ListTipoPiezaSerializer(
                models.TipoPieza.objects.all(), many=True
            ).data,
            "tipos_refaccion": serializers.ListTipoRefaccionSerializer(
                models.TipoRefaccion.objects.all(), many=True
            ).data,
            "proveedores": serializers.ListProveedorSerializer(
                models.Proveedor.objects.all(), many=True
            ).data,
        }
        return Response(data, status=status.HTTP_200_OK)


# ------------ CLASIFICACIÓN ------------------------------------------------
class ClasificacionListAPIView(generics.ListAPIView):
    queryset = models.Clasificacion.objects.all().order_by("nombre")
    serializer_class = serializers.ListClasificacionSerializer


class ClasificacionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Clasificacion.objects.all()
    serializer_class = serializers.DetailClasificacionSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateClasificacionSerializer
        return serializers.DetailClasificacionSerializer


class ClasificacionCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateClasificacionSerializer


# ------------ EDO HERRAMIENTA ----------------------------------------------
class EdoHerramientaListAPIView(generics.ListAPIView):
    queryset = models.EdoHerramienta.objects.all().order_by("nombre")
    serializer_class = serializers.ListEdoHerramientaSerializer


class EdoHerramientaDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.EdoHerramienta.objects.all()
    serializer_class = serializers.DetailEdoHerramientaSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateEdoHerramientaSerializer
        return serializers.DetailEdoHerramientaSerializer


class EdoHerramientaCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateEdoHerramientaSerializer


# ------------ EDO PIEZA ----------------------------------------------------
class EdoPiezaListAPIView(generics.ListAPIView):
    queryset = models.EdoPieza.objects.all().order_by("nombre")
    serializer_class = serializers.ListEdoPiezaSerializer


class EdoPiezaDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.EdoPieza.objects.all()
    serializer_class = serializers.DetailEdoPiezaSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateEdoPiezaSerializer
        return serializers.DetailEdoPiezaSerializer


class EdoPiezaCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateEdoPiezaSerializer


# ------------ EDO REFACCION ------------------------------------------------
class EdoRefaccionListAPIView(generics.ListAPIView):
    queryset = models.EdoRefaccion.objects.all().order_by("nombre")
    serializer_class = serializers.ListEdoRefaccionSerializer


class EdoRefaccionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.EdoRefaccion.objects.all()
    serializer_class = serializers.DetailEdoRefaccionSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateEdoRefaccionSerializer
        return serializers.DetailEdoRefaccionSerializer


class EdoRefaccionCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateEdoRefaccionSerializer


# ------------ TIPO HERRAMIENTA ---------------------------------------------
class TipoHerramientaListAPIView(generics.ListAPIView):
    queryset = models.TipoHerramienta.objects.all().order_by("nombre")
    serializer_class = serializers.ListTipoHerramientaSerializer


class TipoHerramientaDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.TipoHerramienta.objects.all()
    serializer_class = serializers.DetailTipoHerramientaSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateTipoHerramientaSerializer
        return serializers.DetailTipoHerramientaSerializer


class TipoHerramientaCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateTipoHerramientaSerializer


# ------------ TIPO PIEZA ---------------------------------------------------
class TipoPiezaListAPIView(generics.ListAPIView):
    queryset = models.TipoPieza.objects.all().order_by("nombre")
    serializer_class = serializers.ListTipoPiezaSerializer


class TipoPiezaDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.TipoPieza.objects.all()
    serializer_class = serializers.DetailTipoPiezaSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateTipoPiezaSerializer
        return serializers.DetailTipoPiezaSerializer


class TipoPiezaCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateTipoPiezaSerializer


# ------------ TIPO REFACCION -----------------------------------------------
class TipoRefaccionListAPIView(generics.ListAPIView):
    queryset = models.TipoRefaccion.objects.all().order_by("nombre")
    serializer_class = serializers.ListTipoRefaccionSerializer


class TipoRefaccionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.TipoRefaccion.objects.all()
    serializer_class = serializers.DetailTipoRefaccionSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateTipoRefaccionSerializer
        return serializers.DetailTipoRefaccionSerializer


class TipoRefaccionCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateTipoRefaccionSerializer


# ------------ PROVEEDORES --------------------------------------------------
class ProveedorListAPIView(generics.ListAPIView):
    queryset = models.Proveedor.objects.all().order_by("razonsocial")
    serializer_class = serializers.ListProveedorSerializer


class ProveedorDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Proveedor.objects.all()
    serializer_class = serializers.DetailProveedorSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateProveedorSerializer
        return serializers.DetailProveedorSerializer


class ProveedorCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateProveedorSerializer


# ------------ HERRAMIENTAS -------------------------------------------------
class HerramientaListAPIView(generics.ListAPIView):
    queryset = models.Herramienta.objects.select_related("tipo_herramienta").order_by("nombre")
    serializer_class = serializers.ListHerramientaSerializer


class HerramientaDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Herramienta.objects.select_related("tipo_herramienta")
    serializer_class = serializers.DetailHerramientaSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateHerramientaSerializer
        return serializers.DetailHerramientaSerializer


class HerramientaCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateHerramientaSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        herramienta = serializer.save()
        data = serializers.DetailHerramientaSerializer(herramienta).data
        return Response(data, status=status.HTTP_201_CREATED)


# ------------ PIEZAS -------------------------------------------------------
class PiezaListAPIView(generics.ListAPIView):
    serializer_class = serializers.ListPiezaSerializer

    def get_queryset(self):
        qs = models.Pieza.objects.select_related("maquina", "edo_pieza", "tipo_pieza")
        maquina = self.request.query_params.get("maquina")
        if maquina:
            qs = qs.filter(maquina_id=maquina)

        horas_op = (
            RegistroOps.objects
            .filter(
                maquina_id=OuterRef("maquina_id"),
                fechaInicio__gte=OuterRef("fechainstalacion"),
            )
            .values("maquina_id")
            .annotate(total=Sum("horasOperacion"))
            .values("total")
        )

        desgaste = Case(
            When(
                tiempovidautil__gt=0,
                then=Least(
                    Round(
                        ExpressionWrapper(
                            F("_horas_op") * 100.0 / F("tiempovidautil"),
                            output_field=FloatField(),
                        ),
                        1,
                    ),
                    Value(100.0),
                ),
            ),
            default=Value(0.0),
            output_field=FloatField(),
        )

        return (
            qs
            .annotate(_horas_op=Coalesce(Subquery(horas_op), Value(0.0), output_field=FloatField()))
            .annotate(porcentaje_desgaste=desgaste)
            .order_by("nombre")
        )


class PiezaDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Pieza.objects.select_related("maquina", "edo_pieza", "tipo_pieza")
    serializer_class = serializers.DetailPiezaSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdatePiezaSerializer
        return serializers.DetailPiezaSerializer


class PiezaCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreatePiezaSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pieza = serializer.save()
        data = serializers.DetailPiezaSerializer(pieza).data
        return Response(data, status=status.HTTP_201_CREATED)


# ------------ REFACCIONES --------------------------------------------------
class RefaccionListAPIView(generics.ListAPIView):
    queryset = models.Refaccion.objects.select_related("proveedor", "tipo_refaccion", "clasificacion").order_by("nombre")
    serializer_class = serializers.ListRefaccionSerializer


class RefaccionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Refaccion.objects.select_related("proveedor", "tipo_refaccion", "clasificacion")
    serializer_class = serializers.DetailRefaccionSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateRefaccionSerializer
        return serializers.DetailRefaccionSerializer


class RefaccionCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateRefaccionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refaccion = serializer.save()
        data = serializers.DetailRefaccionSerializer(refaccion).data
        return Response(data, status=status.HTTP_201_CREATED)


# ------------ TABLAS DE RELACION / INTERMEDIAS (llave compuesta) ---------
# Estas 3 tienen PK compuesta en la BD (ver Meta.unique_together en
# models.py). DRF no soporta lookup_field de varias columnas, asi que el
# Detail busca el objeto a mano con get_object_or_404 usando los dos
# segmentos de la URL. Cada Detail es independiente, no comparten mixin
# a proposito (para que se puedan tocar por separado sin efectos cruzados).

class RefaccMaquiListAPIView(generics.ListAPIView):
    queryset = models.RefaccMaqui.objects.all()
    serializer_class = serializers.ListRefaccMaquiSerializer


class RefaccMaquiCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateRefaccMaquiSerializer


class RefaccMaquiDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.RefaccMaqui.objects.all()
    serializer_class = serializers.DetailRefaccMaquiSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateRefaccMaquiSerializer
        return serializers.DetailRefaccMaquiSerializer

    def get_object(self):
        obj = generics.get_object_or_404(
            self.get_queryset(),
            maquina=self.kwargs["maquina"],
            refaccion=self.kwargs["refaccion"],
        )
        self.check_object_permissions(self.request, obj)
        return obj


class EstadoHerramientaListAPIView(generics.ListAPIView):
    queryset = models.EstadoHerramienta.objects.all()
    serializer_class = serializers.ListEstadoHerramientaSerializer


class EstadoHerramientaCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateEstadoHerramientaSerializer


class EstadoHerramientaDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.EstadoHerramienta.objects.all()
    serializer_class = serializers.DetailEstadoHerramientaSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateEstadoHerramientaSerializer
        return serializers.DetailEstadoHerramientaSerializer

    def get_object(self):
        obj = generics.get_object_or_404(
            self.get_queryset(),
            herramienta=self.kwargs["herramienta"],
            edo_herramienta=self.kwargs["edo_herramienta"],
        )
        self.check_object_permissions(self.request, obj)
        return obj


class EstadoRefaccionListAPIView(generics.ListAPIView):
    queryset = models.EstadoRefaccion.objects.all()
    serializer_class = serializers.ListEstadoRefaccionSerializer


class EstadoRefaccionCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateEstadoRefaccionSerializer


class EstadoRefaccionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.EstadoRefaccion.objects.all()
    serializer_class = serializers.DetailEstadoRefaccionSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateEstadoRefaccionSerializer
        return serializers.DetailEstadoRefaccionSerializer

    def get_object(self):
        obj = generics.get_object_or_404(
            self.get_queryset(),
            estado_refaccion=self.kwargs["estado_refaccion"],
            refaccion=self.kwargs["refaccion"],
        )
        self.check_object_permissions(self.request, obj)
        return obj

# ------------ MOVIMIENTOS ---------------------------------------------------
class MovimientoListAPIView(APIView):
    """Lista los movimientos de inventario (tabla MOVIMIENTO) mas recientes
    primero, con datos ya legibles de refaccion/orden para la tabla del
    cliente. GET /inventario/v1/movimientos/list/"""

    def get(self, request):
        movimientos = (
            Movimiento.objects
            .select_related("refaccion", "orden_mantenimiento")
            .order_by("-fecha", "-hora", "-numeroregistro")[:200]
        )
        data = [
            {
                "numeroRegistro": m.numeroregistro,
                "descripcion": m.descripcion,
                "fecha": m.fecha.isoformat() if m.fecha else None,
                "hora": m.hora.isoformat() if m.hora else None,
                "tipo": m.tipomovimiento,
                "refaccion": m.refaccion_id,
                "refaccion_nombre": m.refaccion.nombre if m.refaccion_id else None,
                "pieza": m.pieza_id,
                "pieza_nombre": m.pieza.nombre if m.pieza_id else None,
                "pieza_numeroserie": m.pieza.numeroserie if m.pieza_id else None,
                "orden_mantenimiento": m.orden_mantenimiento_id,
            }
            for m in movimientos
        ]
        return Response(data, status=status.HTTP_200_OK)


class RegistrarSalidaRefaccionAPIView(APIView):
    """Da salida a una refaccion del almacen via sp_registrar_salida_refaccion:
    descuenta stock y deja el registro en MOVIMIENTO (tipo INSTA) de forma
    atomica. Cada llamada equivale a la salida de UNA unidad.
    POST /inventario/v2/movimientos/salida-refaccion/
    Body: {"refaccion": 1, "orden": "OMP...", "descripcion": "...",
           "fecha": "2026-08-08", "hora": "10:30:00", "pieza": "SN123"}"""

    def post(self, request):
        refaccion = request.data.get("refaccion")
        orden = request.data.get("orden")
        descripcion = request.data.get("descripcion", "")
        fecha = request.data.get("fecha")
        hora = request.data.get("hora")
        pieza = request.data.get("pieza")

        if not refaccion:
            return Response(
                {"detail": "Falta 'refaccion'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with connection.cursor() as cur:
                cur.callproc(
                    "sp_registrar_salida_refaccion",
                    [refaccion, orden, descripcion, fecha, hora, pieza],
                )
                # El SP termina con un SELECT: stock_resultante,
                # numero_movimiento
                col_names = [c[0] for c in cur.description]
                row = cur.fetchone()
                while cur.nextset():
                    pass
                resultado = dict(zip(col_names, row)) if row else {}
        except OperationalError as e:
            # Los SIGNAL SQLSTATE '45000' del SP (refaccion no existe,
            # stock insuficiente, pieza inexistente) llegan aqui.
            mensaje = e.args[1] if len(e.args) > 1 else str(e)
            return Response({"detail": mensaje}, status=status.HTTP_400_BAD_REQUEST)

        return Response(resultado, status=status.HTTP_200_OK)