from django.urls import path
from . import views
from .views import (ListMaquinariaAPIView,DetailMaquinariaAPIView,maquinaria_list,maquinaria_detail)

app_name = "maquinaria"

urlpatterns = [
    path("ping/", views.PingAPIView.as_view(), name="ping"),
    # =====================================================
    # API REST
    # =====================================================
    # Lista de máquinas
    path("api/v1/list/", ListMaquinariaAPIView.as_view(), name="maquinaria-api-list"),
    
    # Detalle API
    path("api/v1/<str:codigo>/", DetailMaquinariaAPIView.as_view(), name="maquinaria-api-detail"),

    # =====================================================
    # INTERFAZ WEB HTML
    # =====================================================
    # Vista general de maquinaria
    path("", maquinaria_list, name="maquinaria-list"),
    
    # Detalle visual 3D de máquina
    path("<str:codigo>/", maquinaria_detail, name="maquinaria-detail"),

    # v1 / v2 como en las clases de tu maestro, agrega aqui conforme crees
    # tus vistas de list/detail/create/update/delete:
    # path("v1/list/", views.ListMaquinariaAPIView.as_view(), name="list"),
    # path("v1/<int:pk>/", views.DetailMaquinariaAPIView.as_view(), name="detail"),
    # path("v2/create/", views.CreateMaquinariaAPIView.as_view(), name="create"),
]
