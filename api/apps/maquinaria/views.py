from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from . import models
from . import serializers


class PingAPIView(APIView):
    """Endpoint de prueba: confirma que el modulo Maquinaria responde."""

    def get(self, request):
        return Response({"modulo": "maquinaria", "status": "ok"}, status=status.HTTP_200_OK)


# A partir de aqui sigue el patron de tu maestro cuando agregues modelos reales:
#
# class ListMaquinariaAPIView(generics.ListAPIView):
#     queryset = models.MiModelo.objects.all()
#     serializer_class = serializers.ListMaquinaSerializer
#
# class DetailMaquinariaAPIView(generics.RetrieveAPIView):
#     queryset = models.MiModelo.objects.all()
#     serializer_class = serializers.DetailMaquinaSerializer
#
# class CreateMaquinariaAPIView(generics.CreateAPIView):
#     serializer_class = serializers.CreateMaquinaSerializer
#
# class UpdateMaquinariaAPIView(generics.UpdateAPIView):
#     queryset = models.MiModelo.objects.all()
#     serializer_class = serializers.CreateMaquinaSerializer
#
# class DeleteMaquinariaAPIView(generics.DestroyAPIView):
#     queryset = models.MiModelo.objects.all()


from rest_framework import generics

from .models import Maquina
from .serializers import (
    ListMaquinaSerializer,
    DetailMaquinaSerializer
)

import requests
from django.shortcuts import render



# ======================================
# API LISTADO DE MAQUINAS
# ======================================

class ListMaquinariaAPIView(generics.ListAPIView):

    queryset = Maquina.objects.all()

    serializer_class = ListMaquinaSerializer



# ======================================
# API DETALLE DE MAQUINA
# ======================================

class DetailMaquinariaAPIView(generics.RetrieveAPIView):

    queryset = Maquina.objects.all()

    serializer_class = DetailMaquinaSerializer

    lookup_field = "codigo"




# ======================================
# WEB LISTADO DE MAQUINAS
# ======================================

def maquinaria_list(request):

    maquinas = Maquina.objects.all()

    return render(
        request,
        "maquinaria/lista_maquinas.html",
        {
            "maquinas": maquinas
        }
    )



# ======================================
# WEB DETALLE 3D DE MAQUINA
# ======================================

def maquinaria_detail(request, codigo):


    url = ("http://127.0.0.1:8000/"f"api/maquinaria/v1/{codigo}/")
    response = requests.get(url)

    if response.status_code == 200:

        maquina = response.json()
        
    else:
        maquina = {}
        print("ERROR API DETAIL:",response.status_code,response.text)

    return render(
        request,
        "maquinaria/detalle_maquina.html",
        {
            "maquina": maquina
        }
    )