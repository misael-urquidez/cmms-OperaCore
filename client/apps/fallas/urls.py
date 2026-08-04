from django.urls import path

from . import views

app_name = "fallas"

urlpatterns = [
    path("", views.ListaReportes.as_view(), name="index"),
    path("reporte/", views.ReporteFalla.as_view(), name="reporte"),
    path("lista/", views.ListaReportes.as_view(), name="lista"),
    path("detalle/reporte/<int:pk>/", views.DetailReporte.as_view(), name="detalle_reporte"),
    path("actualizar/reporte/<int:pk>/", views.ActualizarReporte.as_view(), name="actualizar_reporte"),
    path("invalidar-cache/reportes/", views.InvalidarCacheReportes.as_view(), name="invalidar_cache_reportes"),
    path("exportar/csv/<int:pk>/", views.ExportarReporteCSV.as_view(), name="exportar_csv"),
    path("exportar/xlsx/<int:pk>/", views.ExportarReporteXLSX.as_view(), name="exportar_xlsx"),
    path("exportar/pdf/<int:pk>/", views.ExportarReportePDF.as_view(), name="exportar_pdf"),
]
