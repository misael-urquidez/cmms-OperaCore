from django.urls import path

from . import views

app_name = "fallas"

urlpatterns = [
    path("ping/", views.PingAPIView.as_view(), name="ping"),
    # v1 - lectura (catalogos + reportes)
    path("v1/tipos-severidad/", views.TipoSeveridadListAPIView.as_view(), name="tipos-severidad"),
    path("v1/tipos-falla/", views.TipoFallaListAPIView.as_view(), name="tipos-falla"),
    path("v1/maquinas/", views.MaquinaListAPIView.as_view(), name="maquinas"),
    path("v1/estados-reporte/", views.EstadoReporteListAPIView.as_view(), name="estados-reporte"),
    path("v2/estados-reporte/create/", views.EstadoReporteCreateAPIView.as_view(), name="estados-reporte-create"),
    path("v2/estados-reporte/<str:codigo>/", views.EstadoReporteDetailAPIView.as_view(), name="estados-reporte-detail"),
    path("v1/catalogos-reporte/", views.CatalogosReporteAPIView.as_view(), name="catalogos-reporte"),
    path("v1/reportes/list/", views.ReporteFallaListAPIView.as_view(), name="reportes-list"),
    # v2 - escritura
    path("v2/tipos-severidad/create/", views.TipoSeveridadCreateAPIView.as_view(), name="tipos-severidad-create"),
    path("v2/tipos-falla/create/", views.TipoFallaCreateAPIView.as_view(), name="tipos-falla-create"),
    path("v2/reportes/create/", views.ReporteFallaCreateAPIView.as_view(), name="reportes-create"),
    # v2 - detalle / edicion / borrado
    path("v2/tipos-severidad/<str:codigo>/", views.TipoSeveridadDetailAPIView.as_view(), name="tipos-severidad-detail"),
    path("v2/tipos-falla/<int:numeroRegistro>/", views.TipoFallaDetailAPIView.as_view(), name="tipos-falla-detail"),

    # ------------ TIPO_REPORTE (llave compuesta) ------------
    path("v1/tipo-reporte/list/", views.TipoReporteListAPIView.as_view(), name="tipo-reporte-list"),
    path("v2/tipo-reporte/create/", views.TipoReporteCreateAPIView.as_view(), name="tipo-reporte-create"),
    path("v1/tipo-reporte/<int:tipo_falla>/<int:reporte_falla>/", views.TipoReporteDetailAPIView.as_view(), name="tipo-reporte-detail"),
]
