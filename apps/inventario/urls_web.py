from django.urls import path

from . import views_web

urlpatterns = [
    path('', views_web.listado_inventario, name='inventario-listado'),
    path('movimiento/nuevo/', views_web.registrar_movimiento, name='inventario-movimiento-nuevo'),
]
