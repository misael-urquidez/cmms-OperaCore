from django.urls import path

from . import views

app_name = "fallas"

urlpatterns = [
    path("ping/", views.PingAPIView.as_view(), name="ping"),
    #---------------- TIPO SEVERIDAD --------------------------------
    path("v1/tipos-severidad/", views.TipoSeveridadListAPIView.as_view(), name="tipos-severidad"),
    path("v2/tipos-severidad/create/", views.TipoSeveridadCreateAPIView.as_view(), name="tipos-severidad-create"),
    path("v2/tipos-severidad/<str:codigo>/", views.TipoSeveridadDetailAPIView.as_view(), name="tipos-severidad-detail"),
    #---------------- TIPO FALLA --------------------------------
    path("v1/tipos-falla/", views.TipoFallaListAPIView.as_view(), name="tipos-falla"),
    path("v2/tipos-falla/create/", views.TipoFallaCreateAPIView.as_view(), name="tipos-falla-create"),
    path("v2/tipos-falla/<int:numeroRegistro>/", views.TipoFallaDetailAPIView.as_view(), name="tipos-falla-detail"),
    #---------------- ESTADO REPORTE--------------------------------
    path("v1/estados-reporte/", views.EstadoReporteListAPIView.as_view(), name="estados-reporte"),
    path("v2/estados-reporte/create/", views.EstadoReporteCreateAPIView.as_view(), name="estados-reporte-create"),
    path("v2/estados-reporte/<str:codigo>/", views.EstadoReporteDetailAPIView.as_view(), name="estados-reporte-detail"),
    #---------------- REPORTE FALLA --------------------------------
    # v1 - lectura (catalogos + reportes)
    path("v1/catalogos-reporte/", views.CatalogosReporteAPIView.as_view(), name="catalogos-reporte"),
    path("v1/reportes/list/", views.ReporteFallaListAPIView.as_view(), name="reportes-list"),
    path("v1/reportes/<int:pk>/", views.ReporteFallaDetailAPIView.as_view(), name="reportes-detail"),
    # v2 - escritura
    path("v2/reportes/create/", views.ReporteFallaCreateAPIView.as_view(), name="reportes-create"),
    path("v2/reportes/update/<int:pk>/", views.ReporteFallaUpdateAPIView.as_view(), name="reportes-update"),
    #---------------- TIPO REPORTE --------------------------------
    path("v1/tipo-reporte/list/", views.TipoReporteListAPIView.as_view(), name="tipo-reporte-list"),
    path("v2/tipo-reporte/create/", views.TipoReporteCreateAPIView.as_view(), name="tipo-reporte-create"),
    path("v1/tipo-reporte/<int:tipo_falla>/<int:reporte_falla>/", views.TipoReporteDetailAPIView.as_view(), name="tipo-reporte-detail"),
    #---------------- EXTRAS --------------------------------
    path("v1/maquinas/", views.MaquinaListAPIView.as_view(), name="maquinas"),
    path("v1/trabajadores/", views.TrabajadorListAPIView.as_view(), name="trabajadores"),
]
