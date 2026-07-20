from django.urls import path

from . import views

app_name = "fallas"

urlpatterns = [
    path("", views.ListaReportes.as_view(), name="index"),
    path("reporte/", views.ReporteFalla.as_view(), name="reporte"),
    path("lista/", views.ListaReportes.as_view(), name="lista"),
    path("detalle/reporte/<int:pk>/", views.DetailReporte.as_view(), name="detalle_reporte"),
]
