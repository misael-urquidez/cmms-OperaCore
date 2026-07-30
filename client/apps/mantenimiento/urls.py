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
    path("ordenes/<str:folio>/update/", views.OrdenUpdateAPIView.as_view(), name="ordenes-update"),
    path("movimientos/crear/", views.MovimientoCrearAPIView.as_view(), name="movimiento-crear"),
    path("exportar/csv/<str:folio>/", views.ExportarOrdenCSV.as_view(), name="exportar_csv"),
    path("exportar/xlsx/<str:folio>/", views.ExportarOrdenXLSX.as_view(), name="exportar_xlsx"),
    path("exportar/pdf/<str:folio>/", views.ExportarOrdenPDF.as_view(), name="exportar_pdf"),
    path("calendario/", views.CalendarioView.as_view(), name="calendario"),
]