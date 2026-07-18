from django.urls import path

from . import views

app_name = "fallas"

urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    #------------TIPO FALLA ----------------------------------------------------------------------------------------
    path("v1/tipo_falla/list/", views.ListTipoFalla.as_view(), name="list_tipos_falla"),
    path("v1/tipo_falla/<int:pk>/", views.DetailTipoFalla.as_view(), name="detail_tipo_falla"),
    path("v1/tipo_falla/create/", views.CreateTipoFalla.as_view(), name="create_tipo_falla"),
    path("v1/tipo_falla/update/<int:pk>/", views.UpdateTipoFalla.as_view(), name="update_tipo_falla"),
    #------------TIPO SEVERIDAD ------------------------------------------------------------------------------------
    path("v1/tipo_severidad/list/", views.ListTipoSeveridad.as_view(), name="list_tipos_severidad"),
    path("v1/tipo_severidad/<int:pk>/", views.DetailTipoSeveridad.as_view(), name="detail_tipo_severidad"),
    path("v1/tipo_severidad/create/", views.CreateTipoSeveridad.as_view(), name="create_tipo_severidad"),
    path("v1/tipo_severidad/update/<int:pk>/", views.UpdateTipoSeveridad.as_view(), name="update_tipo_severidad"),
    #------------EDO REPORTE ---------------------------------------------------------------------------------------
    path("v1/edo_reporte/list/", views.ListEdoReporte.as_view(), name="list_edo_reporte"),
    path("v1/edo_reporte/<int:pk>/", views.DetailEdoReporte.as_view(), name="detail_edo_reporte"),
    path("v1/edo_reporte/create/", views.CreateEdoReporte.as_view(), name="create_edo_reporte"),
    path("v1/edo_reporte/update/<int:pk>/", views.UpdateEdoReporte.as_view(), name="update_edo_reporte"),
    #------------TIPO REPORTE --------------------------------------------------------------------------------------
    path("v1/tipo_reporte/list/", views.ListTipoReporte.as_view(), name="list_tipos_reporte"),
    path("v1/tipo_reporte/<int:pk>/", views.DetailTipoReporte.as_view(), name="detail_tipo_reporte"),
    path("v1/tipo_reporte/create/", views.CreateTipoReporte.as_view(), name="create_tipo_reporte"),
    path("v1/tipo_reporte/update/<int:pk>/", views.UpdateTipoReporte.as_view(), name="update_tipo_reporte"),
    #------------REPORTE FALLA -------------------------------------------------------------------------------------
    path("v1/reporte_falla/list/", views.ListReporteFalla.as_view(), name="list_reportes_falla"),
    path("v1/reporte_falla/<int:pk>/", views.DetailReporteFalla.as_view(), name="detail_reporte_falla"),
    path("v1/reporte_falla/create/", views.CreateReporteFalla.as_view(), name="create_reporte_falla"),
    path("v1/reporte_falla/update/<int:pk>/", views.UpdateReporteFalla.as_view(), name="update_reporte_falla"),
]
