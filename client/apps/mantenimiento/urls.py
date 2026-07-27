from django.urls import path
from . import views
app_name = "mantenimiento"
urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("ordenes/", views.OrdenesListAPIView.as_view(), name="ordenes-datos"),
    path("reportes-disponibles/", views.ReportesDisponiblesAPIView.as_view(), name="reportes-disponibles"),
    path("ordenes/crear/", views.OrdenCrearAPIView.as_view(), name="ordenes-crear"),
    path("ordenes/<str:folio>/asignar/", views.OrdenAsignarAPIView.as_view(), name="ordenes-asignar"),
    path("ordenes/<str:folio>/iniciar/", views.OrdenIniciarAPIView.as_view(), name="ordenes-iniciar"),
    path("ordenes/<str:folio>/cerrar/", views.OrdenCerrarAPIView.as_view(), name="ordenes-cerrar"),
]
