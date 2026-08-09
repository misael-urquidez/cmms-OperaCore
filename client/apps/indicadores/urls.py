from django.urls import path
from . import views

app_name = "indicadores"

urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("kpis/", views.KPIsPage.as_view(), name="kpis"),
    path("rendimiento/", views.RendimientoPage.as_view(), name="rendimiento"),

    path("v1/kpi/<str:vista>/", views.KPIVistaProxy.as_view(), name="kpi_vista"),
    path("v1/resumen/", views.ResumenProxy.as_view(), name="resumen"),
    path("v2/cerrar-periodo/", views.CerrarPeriodoProxy.as_view(), name="cerrar_periodo"),
    path("v1/reporte-disponibilidad/", views.ReporteDisponibilidadProxy.as_view(), name="reporte_disponibilidad"),
    path("v1/rendimiento-trabajadores/", views.RendimientoTrabajadoresProxy.as_view(), name="rendimiento_trabajadores"),
]

urlpatterns += [
    path("v1/reporte/export/<str:formato>/", views.ReporteKPIExportProxy.as_view(), name="reporte_export"),
]