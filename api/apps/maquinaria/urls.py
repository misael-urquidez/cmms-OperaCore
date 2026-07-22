from django.urls import path
from . import views
from .views import *

app_name = "maquinaria"

urlpatterns = [
    path("ping/", PingAPIView.as_view(), name="ping"),
    
    # =====================================================
    # API REST
    # =====================================================
    # Lista de máquinas (Devuelve JSON)
    path("api/v1/list/", ListMaquinariaAPIView.as_view(), name="maquinaria-api-list"),
    path("api/v1/create/", CreateMaquinariaAPIView.as_view(), name="maquinaria-api-create"),
    # Detalle API por código (Devuelve JSON)
    path("api/v1/<str:codigo>/", DetailMaquinariaAPIView.as_view(), name="maquinaria-api-detail"),
]