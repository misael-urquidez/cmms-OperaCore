from django.urls import path

from . import views

app_name = "elipse"

urlpatterns = [
    path("chat/", views.ElipseChatAPIView.as_view(), name="chat"),
    path("sugerencias/", views.ElipseSugerenciasAPIView.as_view(), name="sugerencias"),
    path("autocompletar-falla/", views.ElipseAutocompletarFallaAPIView.as_view(), name="autocompletar_falla"),
]
