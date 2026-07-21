from django.urls import path

from . import views

app_name = "fallas"

urlpatterns = [
    path("ping/", views.PingAPIView.as_view(), name="ping"),
<<<<<<< HEAD
    #------------TIPO FALLA ----------------------------------------------------------------------------------------
    path("v1/tipo_falla/list/", views.ListarTipoFallaAPIView.as_view(), name="list_tipos_falla"),
    path("v1/tipo_falla/create/", views.CrearTipoFallaAPIView.as_view(), name="create_tipo_falla"),
    path("v1/tipo_falla/<int:pk>/", views.DetailTipoFallaAPIView.as_view(), name="detail_tipo_falla"),
    path("v1/tipo_falla/update/<int:pk>/", views.UpdateTipoFallaAPIView.as_view(), name="update_tipo_falla"),
    #------------TIPO SEVERIDAD ------------------------------------------------------------------------------------
    path("v1/tipo_severidad/list/", views.ListarTipoSeveridadAPIView.as_view(), name="list_tipos_severidad"),
    path("v1/tipo_severidad/create/", views.CrearTipoSeveridadAPIView.as_view(), name="create_tipo_severidad"),
    path("v1/tipo_severidad/<str:codigo>/", views.DetailTipoSeveridadAPIView.as_view(), name="detail_tipo_severidad"),
    path("v1/tipo_severidad/update/<str:codigo>/", views.UpdateTipoSeveridadAPIView.as_view(), name="update_tipo_severidad"),
    #------------EDO REPORTE ----------------------------------------------------------------------------------------
    path("v1/edo_reporte/list/", views.ListarEdoReporteAPIView.as_view(), name="list_edos_reporte"),
    path("v1/edo_reporte/create/", views.CrearEdoReporteAPIView.as_view(), name="create_edo_reporte"),
    path("v1/edo_reporte/<str:codigo>/", views.DetailEdoReporteAPIView.as_view(), name="detail_edo_reporte"),
    path("v1/edo_reporte/update/<str:codigo>/", views.UpdateEdoReporteAPIView.as_view(), name="update_edo_reporte"),
    #------------TIPO REPORTE ----------------------------------------------------------------------------------------
    path("v1/tipo_reporte/list/", views.ListarTipoReporteAPIView.as_view(), name="list_tipos_reporte"),
    path("v1/tipo_reporte/create/", views.CrearTipoReporteAPIView.as_view(), name="create_tipo_reporte"),
    path("v1/tipo_reporte/<int:tipo_falla>/", views.DetailTipoReporteAPIView.as_view(), name="detail_tipo_reporte"),
    path("v1/tipo_reporte/update/<int:tipo_falla>/", views.UpdateTipoReporteAPIView.as_view(), name="update_tipo_reporte"),
    #------------REPORTE FALLA ---------------------------------------------------------------------------------------
    path("v1/reportes/list/", views.ListarReporteFallaAPIView.as_view(), name="list_reportes"),
    path("v1/reportes/create/", views.CrearReporteFallaAPIView.as_view(), name="create_reporte"),
    path("v1/reportes/<int:pk>/", views.DetailReporteFallaAPIView.as_view(), name="detail_reporte"),
    path("v1/reportes/update/<int:pk>/", views.UpdateReporteFallaAPIView.as_view(), name="update_reporte"),
=======
    # v1 - lectura (catalogos + reportes)
    path("v1/tipos-severidad/", views.TipoSeveridadListAPIView.as_view(), name="tipos-severidad"),
    path("v1/tipos-falla/", views.TipoFallaListAPIView.as_view(), name="tipos-falla"),
    path("v1/maquinas/", views.MaquinaListAPIView.as_view(), name="maquinas"),
    path("v1/estados-reporte/", views.EstadoReporteListAPIView.as_view(), name="estados-reporte"),
    path("v1/catalogos-reporte/", views.CatalogosReporteAPIView.as_view(), name="catalogos-reporte"),
    path("v1/reportes/list/", views.ReporteFallaListAPIView.as_view(), name="reportes-list"),
    # v2 - escritura
    path("v2/reportes/create/", views.ReporteFallaCreateAPIView.as_view(), name="reportes-create"),
    
>>>>>>> origin/main
]
