from django.urls import path

from . import views

app_name = "elipse"

urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("chat/", views.Chat.as_view(), name="chat"),
    path("estado/", views.Estado.as_view(), name="estado"),
    path("sugerencias/", views.Sugerencias.as_view(), name="sugerencias"),
    path("autocompletar-falla/", views.AutocompletarFalla.as_view(), name="autocompletar_falla"),
    path("autocompletar-orden/", views.AutocompletarOrden.as_view(), name="autocompletar_orden"),
    path("sugerencia-diagnostico/", views.SugerenciaDiagnostico.as_view(), name="sugerencia_diagnostico"),
]