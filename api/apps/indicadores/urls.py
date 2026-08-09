from django.urls import path
from . import views

app_name = "indicadores"

urlpatterns = [
    path("ping/", views.PingAPIView.as_view(), name="ping"),
    path("v1/resumen/", views.ResumenIndicadoresAPIView.as_view(), name="resumen"),

    path("v1/kpi/<str:vista>/", views.KPIVistaAPIView.as_view(), name="kpi_vista"),
    path("v1/reporte-disponibilidad/", views.ReporteDisponibilidadPlantaAPIView.as_view(), name="reporte_disponibilidad"),
    path("v2/cerrar-periodo/", views.CerrarPeriodoIndicadorAPIView.as_view(), name="cerrar_periodo"),
]

urlpatterns += [
    path("v1/reporte/export/<str:formato>/", views.ReporteKPIExportAPIView.as_view(), name="reporte_export"),
]
