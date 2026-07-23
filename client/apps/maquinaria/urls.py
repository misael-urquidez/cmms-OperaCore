from django.urls import path
from . import views

app_name = "maquinaria"

urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("listar/", views.ListarMaquinas.as_view(), name="listar"),
    path("crear/", views.CrearMaquina.as_view(), name="crear_maquina"), 
    path("<str:codigo>/", views.DetalleMaquina.as_view(), name="detail"), 
]