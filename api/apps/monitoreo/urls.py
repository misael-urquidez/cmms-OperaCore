from django.urls import path

from . import views

app_name = "monitoreo"

urlpatterns = [
    path("lecturas/", views.LecturaCreateAPIView.as_view(), name="lecturas"),
    path("maquinas/", views.MaquinaListAPIView.as_view(), name="maquinas"),
    path("maquinas/<str:codigo>/indicadores/", views.IndicadoresMaquinaAPIView.as_view(), name="indicadores"),
    path("maquinas/<str:codigo>/estado/", views.EstadoMaquinaAPIView.as_view(), name="estado"),
    path("maquinas/<str:codigo>/historial/", views.HistorialLecturasAPIView.as_view(), name="historial"),
    path("maquinas/crear/", views.CrearMaquinaAPIView.as_view(), name="crear-maquina"),
    path("catalogos/", views.CatalogosMaquinaAPIView.as_view(), name="catalogos"),
    path("reportar-falla/", views.ReportarFallaManualAPIView.as_view(), name="reportar-falla"),
    path("maquinas/<str:codigo>/modo/", views.ModoMonitoreoAPIView.as_view(), name="modo-monitoreo"),
    path("maquinas/<str:codigo>/simular/", views.SimularLecturaAPIView.as_view(), name="simular-lectura"),
    path("maquinas/<str:codigo>/registro-ops/", views.RegistroOpsAPIView.as_view(), name="registro-ops"),
]
