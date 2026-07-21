from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from . import models
from . import serializers


class PingAPIView(APIView):
    """Endpoint de prueba: confirma que el modulo Inventario responde."""

    def get(self, request):
        return Response({"modulo": "inventario", "status": "ok"}, status=status.HTTP_200_OK)

# ------------ CLASIFICACION ----------------------------------------------------
class ListarClasificacionAPIView(generics.ListAPIView):
    queryset = models.Clasificacion.objects.all()
    serializer_class = serializers.ListClasificacionSerializer

class DetailClasificacionAPIView(generics.RetrieveAPIView):
    queryset = models.Clasificacion.objects.all()
    serializer_class = serializers.DetailClasificacionSerializer
    lookup_field = 'codigo'

class CrearClasificacionAPIView(generics.CreateAPIView):
    queryset = models.Clasificacion.objects.all()
    serializer_class = serializers.CreateClasificacionSerializer

class UpdateClasificacionAPIView(generics.UpdateAPIView):
    queryset = models.Clasificacion.objects.all()
    serializer_class = serializers.UpdateClasificacionSerializer
    lookup_field = 'codigo'


# ------------ EDO HERRAMIENTA --------------------------------------------------
class ListarEdoHerramientaAPIView(generics.ListAPIView):
    queryset = models.EdoHerramienta.objects.all()
    serializer_class = serializers.ListEdoHerramientaSerializer

class DetailEdoHerramientaAPIView(generics.RetrieveAPIView):
    queryset = models.EdoHerramienta.objects.all()
    serializer_class = serializers.DetailEdoHerramientaSerializer
    lookup_field = 'codigo'

class CrearEdoHerramientaAPIView(generics.CreateAPIView):
    queryset = models.EdoHerramienta.objects.all()
    serializer_class = serializers.CreateEdoHerramientaSerializer

class UpdateEdoHerramientaAPIView(generics.UpdateAPIView):
    queryset = models.EdoHerramienta.objects.all()
    serializer_class = serializers.UpdateEdoHerramientaSerializer
    lookup_field = 'codigo'


# ------------ EDO PIEZA --------------------------------------------------------
class ListarEdoPiezaAPIView(generics.ListAPIView):
    queryset = models.EdoPieza.objects.all()
    serializer_class = serializers.ListEdoPiezaSerializer

class DetailEdoPiezaAPIView(generics.RetrieveAPIView):
    queryset = models.EdoPieza.objects.all()
    serializer_class = serializers.DetailEdoPiezaSerializer
    lookup_field = 'codigo'

class CrearEdoPiezaAPIView(generics.CreateAPIView):
    queryset = models.EdoPieza.objects.all()
    serializer_class = serializers.CreateEdoPiezaSerializer

class UpdateEdoPiezaAPIView(generics.UpdateAPIView):
    queryset = models.EdoPieza.objects.all()
    serializer_class = serializers.UpdateEdoPiezaSerializer
    lookup_field = 'codigo'


# ------------ EDO REFACCION ----------------------------------------------------
class ListarEdoRefaccionAPIView(generics.ListAPIView):
    queryset = models.EdoRefaccion.objects.all()
    serializer_class = serializers.ListEdoRefaccionSerializer

class DetailEdoRefaccionAPIView(generics.RetrieveAPIView):
    queryset = models.EdoRefaccion.objects.all()
    serializer_class = serializers.DetailEdoRefaccionSerializer
    lookup_field = 'codigo'

class CrearEdoRefaccionAPIView(generics.CreateAPIView):
    queryset = models.EdoRefaccion.objects.all()
    serializer_class = serializers.CreateEdoRefaccionSerializer

class UpdateEdoRefaccionAPIView(generics.UpdateAPIView):
    queryset = models.EdoRefaccion.objects.all()
    serializer_class = serializers.UpdateEdoRefaccionSerializer
    lookup_field = 'codigo'


# ------------ TIPO HERRAMIENTA --------------------------------------------------
class ListarTipoHerramientaAPIView(generics.ListAPIView):
    queryset = models.TipoHerramienta.objects.all()
    serializer_class = serializers.ListTipoHerramientaSerializer

class DetailTipoHerramientaAPIView(generics.RetrieveAPIView):
    queryset = models.TipoHerramienta.objects.all()
    serializer_class = serializers.DetailTipoHerramientaSerializer

class CrearTipoHerramientaAPIView(generics.CreateAPIView):
    queryset = models.TipoHerramienta.objects.all()
    serializer_class = serializers.CreateTipoHerramientaSerializer

class UpdateTipoHerramientaAPIView(generics.UpdateAPIView):
    queryset = models.TipoHerramienta.objects.all()
    serializer_class = serializers.UpdateTipoHerramientaSerializer


# ------------ TIPO PIEZA --------------------------------------------------------
class ListarTipoPiezaAPIView(generics.ListAPIView):
    queryset = models.TipoPieza.objects.all()
    serializer_class = serializers.ListTipoPiezaSerializer

class DetailTipoPiezaAPIView(generics.RetrieveAPIView):
    queryset = models.TipoPieza.objects.all()
    serializer_class = serializers.DetailTipoPiezaSerializer

class CrearTipoPiezaAPIView(generics.CreateAPIView):
    queryset = models.TipoPieza.objects.all()
    serializer_class = serializers.CreateTipoPiezaSerializer

class UpdateTipoPiezaAPIView(generics.UpdateAPIView):
    queryset = models.TipoPieza.objects.all()
    serializer_class = serializers.UpdateTipoPiezaSerializer


# ------------ TIPO REFACCION ----------------------------------------------------
class ListarTipoRefaccionAPIView(generics.ListAPIView):
    queryset = models.TipoRefaccion.objects.all()
    serializer_class = serializers.ListTipoRefaccionSerializer

class DetailTipoRefaccionAPIView(generics.RetrieveAPIView):
    queryset = models.TipoRefaccion.objects.all()
    serializer_class = serializers.DetailTipoRefaccionSerializer

class CrearTipoRefaccionAPIView(generics.CreateAPIView):
    queryset = models.TipoRefaccion.objects.all()
    serializer_class = serializers.CreateTipoRefaccionSerializer

class UpdateTipoRefaccionAPIView(generics.UpdateAPIView):
    queryset = models.TipoRefaccion.objects.all()
    serializer_class = serializers.UpdateTipoRefaccionSerializer


# ------------ PROVEEDOR --------------------------------------------------------
class ListarProveedorAPIView(generics.ListAPIView):
    queryset = models.Proveedor.objects.all()
    serializer_class = serializers.ListProveedorSerializer

class DetailProveedorAPIView(generics.RetrieveAPIView):
    queryset = models.Proveedor.objects.all()
    serializer_class = serializers.DetailProveedorSerializer
    lookup_field = 'codigo'

class CrearProveedorAPIView(generics.CreateAPIView):
    queryset = models.Proveedor.objects.all()
    serializer_class = serializers.CreateProveedorSerializer

class UpdateProveedorAPIView(generics.UpdateAPIView):
    queryset = models.Proveedor.objects.all()
    serializer_class = serializers.UpdateProveedorSerializer
    lookup_field = 'codigo'


# ------------ HERRAMIENTA -------------------------------------------------------
class ListarHerramientaAPIView(generics.ListAPIView):
    queryset = models.Herramienta.objects.all()
    serializer_class = serializers.ListHerramientaSerializer

class DetailHerramientaAPIView(generics.RetrieveAPIView):
    queryset = models.Herramienta.objects.all()
    serializer_class = serializers.DetailHerramientaSerializer

class CrearHerramientaAPIView(generics.CreateAPIView):
    queryset = models.Herramienta.objects.all()
    serializer_class = serializers.CreateHerramientaSerializer

class UpdateHerramientaAPIView(generics.UpdateAPIView):
    queryset = models.Herramienta.objects.all()
    serializer_class = serializers.UpdateHerramientaSerializer


# ------------ PIEZA ------------------------------------------------------------
class ListarPiezaAPIView(generics.ListAPIView):
    queryset = models.Pieza.objects.all()
    serializer_class = serializers.ListPiezaSerializer

class DetailPiezaAPIView(generics.RetrieveAPIView):
    queryset = models.Pieza.objects.all()
    serializer_class = serializers.DetailPiezaSerializer
    lookup_field = 'numeroserie'  # <-- Tu PK de texto en Pieza

class CrearPiezaAPIView(generics.CreateAPIView):
    queryset = models.Pieza.objects.all()
    serializer_class = serializers.CreatePiezaSerializer

class UpdatePiezaAPIView(generics.UpdateAPIView):
    queryset = models.Pieza.objects.all()
    serializer_class = serializers.UpdatePiezaSerializer
    lookup_field = 'numeroserie'


# ------------ REFACCION --------------------------------------------------------
class ListarRefaccionAPIView(generics.ListAPIView):
    queryset = models.Refaccion.objects.all()
    serializer_class = serializers.ListRefaccionSerializer

class DetailRefaccionAPIView(generics.RetrieveAPIView):
    queryset = models.Refaccion.objects.all()
    serializer_class = serializers.DetailRefaccionSerializer

class CrearRefaccionAPIView(generics.CreateAPIView):
    queryset = models.Refaccion.objects.all()
    serializer_class = serializers.CreateRefaccionSerializer

class UpdateRefaccionAPIView(generics.UpdateAPIView):
    queryset = models.Refaccion.objects.all()
    serializer_class = serializers.UpdateRefaccionSerializer


# ------------ TABLAS DE RELACION / INTERMEDIAS ---------------------------------
class ListarRefaccMaquiAPIView(generics.ListAPIView):
    queryset = models.RefaccMaqui.objects.all()
    serializer_class = serializers.ListRefaccMaquiSerializer

class DetailRefaccMaquiAPIView(generics.RetrieveAPIView):
    queryset = models.RefaccMaqui.objects.all()
    serializer_class = serializers.DetailRefaccMaquiSerializer
    lookup_field = 'maquina'

class CrearRefaccMaquiAPIView(generics.CreateAPIView):
    queryset = models.RefaccMaqui.objects.all()
    serializer_class = serializers.CreateRefaccMaquiSerializer

class UpdateRefaccMaquiAPIView(generics.UpdateAPIView):
    queryset = models.RefaccMaqui.objects.all()
    serializer_class = serializers.UpdateRefaccMaquiSerializer
    lookup_field = 'maquina'


class ListarEstadoHerramientaAPIView(generics.ListAPIView):
    queryset = models.EstadoHerramienta.objects.all()
    serializer_class = serializers.ListEstadoHerramientaSerializer

class DetailEstadoHerramientaAPIView(generics.RetrieveAPIView):
    queryset = models.EstadoHerramienta.objects.all()
    serializer_class = serializers.DetailEstadoHerramientaSerializer
    lookup_field = 'herramienta'

class CrearEstadoHerramientaAPIView(generics.CreateAPIView):
    queryset = models.EstadoHerramienta.objects.all()
    serializer_class = serializers.CreateEstadoHerramientaSerializer

class UpdateEstadoHerramientaAPIView(generics.UpdateAPIView):
    queryset = models.EstadoHerramienta.objects.all()
    serializer_class = serializers.UpdateEstadoHerramientaSerializer
    lookup_field = 'herramienta'


class ListarEstadoRefaccionAPIView(generics.ListAPIView):
    queryset = models.EstadoRefaccion.objects.all()
    serializer_class = serializers.ListEstadoRefaccionSerializer

class DetailEstadoRefaccionAPIView(generics.RetrieveAPIView):
    queryset = models.EstadoRefaccion.objects.all()
    serializer_class = serializers.DetailEstadoRefaccionSerializer
    lookup_field = 'estado_refaccion'

class CrearEstadoRefaccionAPIView(generics.CreateAPIView):
    queryset = models.EstadoRefaccion.objects.all()
    serializer_class = serializers.CreateEstadoRefaccionSerializer

class UpdateEstadoRefaccionAPIView(generics.UpdateAPIView):
    queryset = models.EstadoRefaccion.objects.all()
    serializer_class = serializers.UpdateEstadoRefaccionSerializer
    lookup_field = 'estado_refaccion'
