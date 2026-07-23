from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from . import models
from . import serializers


class PingAPIView(APIView):
    """Endpoint de prueba: confirma que el modulo Maquinaria responde."""

    def get(self, request):
        return Response({"modulo": "maquinaria", "status": "ok"}, status=status.HTTP_200_OK)

#------------PLANTA-----------------------------------------------------
class ListarPlantaAPIView(generics.ListAPIView):
    queryset = models.Planta.objects.all()
    serializer_class = serializers.ListPlantaSerializer

class DetailPlantaAPIView(generics.RetrieveAPIView):
    queryset = models.Planta.objects.all()
    serializer_class = serializers.DetailPlantaSerializer
    lookup_field = 'codigo'

class CrearPlantaAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreatePlantaSerializer

class UpdatePlantaAPIView(generics.UpdateAPIView):
    queryset = models.Planta.objects.all()
    serializer_class = serializers.UpdatePlantaSerializer
    lookup_field = 'codigo'

# ------------ AREA ------------------------------------------------------
class ListarAreaAPIView(generics.ListAPIView):
    queryset = models.Area.objects.all()
    serializer_class = serializers.ListAreaSerializer

class DetailAreaAPIView(generics.RetrieveAPIView):
    queryset = models.Area.objects.all()
    serializer_class = serializers.DetailAreaSerializer
    lookup_field = 'codigo'

class CrearAreaAPIView(generics.CreateAPIView):
    queryset = models.Area.objects.all()
    serializer_class = serializers.CreateAreaSerializer

class UpdateAreaAPIView(generics.UpdateAPIView):
    queryset = models.Area.objects.all()
    serializer_class = serializers.UpdateAreaSerializer
    lookup_field = 'codigo'


# ------------ EDO MAQUINA -----------------------------------------------
class ListarEdoMaquinaAPIView(generics.ListAPIView):
    queryset = models.EdoMaquina.objects.all()
    serializer_class = serializers.ListEdoMaquinaSerializer

class DetailEdoMaquinaAPIView(generics.RetrieveAPIView):
    queryset = models.EdoMaquina.objects.all()
    serializer_class = serializers.DetailEdoMaquinaSerializer
    lookup_field = 'codigo'

class CrearEdoMaquinaAPIView(generics.CreateAPIView):
    queryset = models.EdoMaquina.objects.all()
    serializer_class = serializers.CreateEdoMaquinaSerializer

class UpdateEdoMaquinaAPIView(generics.UpdateAPIView):
    queryset = models.EdoMaquina.objects.all()
    serializer_class = serializers.UpdateEdoMaquinaSerializer
    lookup_field = 'codigo'


# ------------ LINEA -----------------------------------------------------
class ListarLineaAPIView(generics.ListAPIView):
    queryset = models.Linea.objects.all()
    serializer_class = serializers.ListLineaSerializer

class DetailLineaAPIView(generics.RetrieveAPIView):
    queryset = models.Linea.objects.all()
    serializer_class = serializers.DetailLineaSerializer
    lookup_field = 'codigo'

class CrearLineaAPIView(generics.CreateAPIView):
    queryset = models.Linea.objects.all()
    serializer_class = serializers.CreateLineaSerializer

class UpdateLineaAPIView(generics.UpdateAPIView):
    queryset = models.Linea.objects.all()
    serializer_class = serializers.UpdateLineaSerializer
    lookup_field = 'codigo'


# ------------ MARCA -----------------------------------------------------
class ListarMarcaAPIView(generics.ListAPIView):
    queryset = models.Marca.objects.all()
    serializer_class = serializers.ListMarcaSerializer

class DetailMarcaAPIView(generics.RetrieveAPIView):
    queryset = models.Marca.objects.all()
    serializer_class = serializers.DetailMarcaSerializer
    lookup_field = 'clave'  # <-- Ojo: Aquí tu PK en el serializer se llama 'clave'

class CrearMarcaAPIView(generics.CreateAPIView):
    queryset = models.Marca.objects.all()
    serializer_class = serializers.CreateMarcaSerializer

class UpdateMarcaAPIView(generics.UpdateAPIView):
    queryset = models.Marca.objects.all()
    serializer_class = serializers.UpdateMarcaSerializer
    lookup_field = 'clave'


# ------------ MODELO ----------------------------------------------------
class ListarModeloAPIView(generics.ListAPIView):
    queryset = models.Modelo.objects.all()
    serializer_class = serializers.ListModeloSerializer

class DetailModeloAPIView(generics.RetrieveAPIView):
    queryset = models.Modelo.objects.all()
    serializer_class = serializers.DetailModeloSerializer
    lookup_field = 'codigo'

class CrearModeloAPIView(generics.CreateAPIView):
    queryset = models.Modelo.objects.all()
    serializer_class = serializers.CreateModeloSerializer

class UpdateModeloAPIView(generics.UpdateAPIView):
    queryset = models.Modelo.objects.all()
    serializer_class = serializers.UpdateModeloSerializer
    lookup_field = 'codigo'


# ------------ TIPO MAQUINA ----------------------------------------------
class ListarTipoMaquinaAPIView(generics.ListAPIView):
    queryset = models.TipoMaquina.objects.all()
    serializer_class = serializers.ListTipoMaquinaSerializer

class DetailTipoMaquinaAPIView(generics.RetrieveAPIView):
    queryset = models.TipoMaquina.objects.all()
    serializer_class = serializers.DetailTipoMaquinaSerializer
    # Si numeroregistro es un AutoField entero, no requieres configurar obligatoriamente el lookup_field aquí.
    # Pero si es pk tipo texto, descomenta la siguiente línea:
    # lookup_field = 'numeroregistro' 

class CrearTipoMaquinaAPIView(generics.CreateAPIView):
    queryset = models.TipoMaquina.objects.all()
    serializer_class = serializers.CreateTipoMaquinaSerializer

class UpdateTipoMaquinaAPIView(generics.UpdateAPIView):
    queryset = models.TipoMaquina.objects.all()
    serializer_class = serializers.UpdateTipoMaquinaSerializer


# ------------ MAQUINA ---------------------------------------------------
class ListarMaquinaAPIView(generics.ListAPIView):
    queryset = models.Maquina.objects.all()
    serializer_class = serializers.ListMaquinaSerializer

class DetailMaquinaAPIView(generics.RetrieveAPIView):
    queryset = models.Maquina.objects.all()
    serializer_class = serializers.DetailMaquinaSerializer
    lookup_field = 'codigo'

class CrearMaquinaAPIView(generics.CreateAPIView):
    queryset = models.Maquina.objects.all()
    serializer_class = serializers.CreateMaquinaSerializer

class UpdateMaquinaAPIView(generics.UpdateAPIView):
    queryset = models.Maquina.objects.all()
    serializer_class = serializers.UpdateMaquinaSerializer
    lookup_field = 'codigo'

# ------------ REGISTRO OPERACIONES------------------------------------------------

class ListRegistroOpsView(generics.ListAPIView):
    queryset = models.RegistroOps.objects.all().order_by("-numeroregistro")
    serializer_class = serializers.ListRegistroOpsSerializer

class CreateRegistroOpsView(generics.CreateAPIView):
    queryset = models.RegistroOps.objects.all()
    serializer_class = serializers.CreateRegistroOpsSerializer

class DetailRegistroOpsView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.RegistroOps.objects.all()
    lookup_field = "numeroregistro"

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.CreateRegistroOpsSerializer
        return serializers.DetailRegistroOpsSerializer

# ------------ INDICADOR ------------------------------------------------
class IndicadorListAPIView(generics.ListAPIView):
    queryset = models.Indicador.objects.all().order_by("-numeroregistro")
    serializer_class = serializers.ListIndicadorSerializer


class IndicadorCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateIndicadorSerializer


class IndicadorDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Indicador.objects.all()
    lookup_field = "numeroregistro"

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return serializers.CreateIndicadorSerializer
        return serializers.DetailIndicadorSerializer