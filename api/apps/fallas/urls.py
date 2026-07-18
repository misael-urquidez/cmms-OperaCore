from django.urls import path

from . import views

app_name = "fallas"

urlpatterns = [
    path("ping/", views.PingAPIView.as_view(), name="ping"),
    #------------TIPO FALLA ----------------------------------------------------------------------------------------
    path("v1/tipo_falla/list/", views.ListarReportesFallasAPIView.as_view(), name="list_tipos_falla"),
    path("v1/tipo_falla/<int:pk>/", views.DetailReporteFallaAPIView.as_view(), name="detail_tipo_falla"),
    path("v1/tipo_falla/create/", views.CrearReporteFallaAPIView.as_view(), name="create_tipo_falla"),
    path("v1/tipo_falla/update/<int:pk>/", views.UpdateReporteFallaAPIView.as_view(), name="update_tipo_falla"),
    #------------TIPO SEVERIDAD ------------------------------------------------------------------------------------
    path("v1/tipo_severidad/list/", views.ListarTipoSeveridadAPIView.as_view(), name="list_tipos_severidad"),
    path("v1/tipo_severidad/<int:pk>/", views.DetailTipoSeveridadAPIView.as_view(), name="detail_tipo_severidad"),
    path("v1/tipo_severidad/create/", views.CrearTipoSeveridadAPIView.as_view(), name="create_tipo_severidad"),
    path("v1/tipo_severidad/update/<int:pk>/", views.UpdateTipoSeveridadAPIView.as_view(), name="update_tipo_severidad"),
    #------------EDO REPORTE ----------------------------------------------------------------------------------------
    path("v1/edo_reporte/list/", views.ListarEdoReporteAPIView.as_view(), name="list_edos_reporte"),
    path("v1/edo_reporte/<int:pk>/", views.DetailEdoReporteAPIView.as_view(), name="detail_edo_reporte"),
    path("v1/edo_reporte/create/", views.CrearEdoReporteAPIView.as_view(), name="create_edo_reporte"),
    path("v1/edo_reporte/update/<int:pk>/", views.UpdateEdoReporteAPIView.as_view(), name="update_edo_reporte"),
    #------------TIPO REPORTE ----------------------------------------------------------------------------------------
    path("v1/tipo_reporte/list/", views.ListarTipoReporteAPIView.as_view(), name="list_tipos_reporte"),
    path("v1/tipo_reporte/<int:pk>/", views.DetailTipoReporteAPIView.as_view(), name="detail_tipo_reporte"),
    path("v1/tipo_reporte/create/", views.CrearTipoReporteAPIView.as_view(), name="create_tipo_reporte"),
    path("v1/tipo_reporte/update/<int:pk>/", views.UpdateTipoReporteAPIView.as_view(), name="update_tipo_reporte"),
    #------------REPORTE FALLA ---------------------------------------------------------------------------------------
    path("v1/reportes/list/", views.ListarReportesFallasAPIView.as_view(), name="list_reportes"),
    path("v1/reportes/<int:pk>/", views.DetailReporteFallaAPIView.as_view(), name="detail_reporte"),
    path("v1/reportes/create/", views.CrearReporteFallaAPIView.as_view(), name="create_reporte"),
    path("v1/reportes/update/<int:pk>/", views.UpdateReporteFallaAPIView.as_view(), name="update_reporte"),
]
