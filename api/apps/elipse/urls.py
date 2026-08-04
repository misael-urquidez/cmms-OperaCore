from django.urls import path

from . import views

app_name = "elipse"

urlpatterns = [
    path("chat/", views.ElipseChatAPIView.as_view(), name="chat"),
    path("estado/", views.ElipseEstadoAPIView.as_view(), name="estado"),
    path("sugerencias/", views.ElipseSugerenciasAPIView.as_view(), name="sugerencias"),
    path("autocompletar-falla/", views.ElipseAutocompletarFallaAPIView.as_view(), name="autocompletar_falla"),
    path("autocompletar-orden/", views.ElipseAutocompletarOrdenAPIView.as_view(), name="autocompletar_orden"),
    path("sugerencia-diagnostico/", views.ElipseSugerenciaDiagnosticoAPIView.as_view(), name="sugerencia_diagnostico"),
]