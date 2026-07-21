from django.urls import path
from . import views

app_name = "inventario"

urlpatterns = [
    path("", views.ListadoInventario.as_view(), name="listado"),
    path("movimiento/nuevo/", views.RegistrarMovimiento.as_view(), name="movimiento_nuevo"),
]
