from django.urls import path
from . import views

app_name = "indicadores"

urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("kpis/", views.KPIsPage.as_view(), name="kpis"),

    path("v1/kpi/<str:vista>/", views.KPIVistaProxy.as_view(), name="kpi_vista"),
    path("v1/resumen/", views.ResumenProxy.as_view(), name="resumen"),
]

urlpatterns += [
    path("v1/reporte/export/<str:formato>/", views.ReporteKPIExportProxy.as_view(), name="reporte_export"),
]