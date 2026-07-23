from django.urls import path

from . import views

app_name = "monitoreo"

urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("datos/", views.DatosMaquinasAPIView.as_view(), name="datos"),
    path("catalogos/", views.CatalogosMaquinaAPIView.as_view(), name="catalogos"),
    path("maquinas/crear/", views.CrearMaquinaAPIView.as_view(), name="crear-maquina"),
    path("maquinas/<str:codigo>/indicadores/", views.IndicadoresMaquinaAPIView.as_view(), name="indicadores"),
    path("maquinas/<str:codigo>/historial/", views.HistorialMaquinaAPIView.as_view(), name="historial"),
    path("maquinas/<str:codigo>/estado/", views.EstadoMaquinaAPIView.as_view(), name="estado"),
    path("maquinas/<str:codigo>/modo/", views.ModoMonitoreoAPIView.as_view(), name="modo"),
    path("lecturas/manual/", views.LecturaManualAPIView.as_view(), name="lectura-manual"),
    path("maquinas/<str:codigo>/simular/", views.SimularLecturaAPIView.as_view(), name="simular"),
    path("maquinas/<str:codigo>/registro-ops/", views.RegistroOpsAPIView.as_view(), name="registro-ops"),
]
