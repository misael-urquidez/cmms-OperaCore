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

# ------------ REGISTRO DE OPERACION -------------------------------------
class ListarRegistroOpsAPIView(generics.ListAPIView):
    queryset = models.RegistroOps.objects.all()
    serializer_class = serializers.ListRegistroOpsSerarializar

class DetailRegistroOpsAPIView(generics.RetrieveAPIView):
    queryset = models.RegistroOps.objects.all()
    serializer_class = serializers.DetailRegistroOpsSerarializar

class CrearRegistroOpsAPIView(generics.CreateAPIView):
    queryset = models.RegistroOps.objects.all()
    serializer_class = serializers.CreateRegistroOpsSerarializar

class UpdateRegistroOpsAPIView(generics.UpdateAPIView):
    queryset = models.RegistroOps.objects.all()
    serializer_class = serializers.UpdateRegistroOpsSerarializar