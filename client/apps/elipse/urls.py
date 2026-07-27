from django.urls import path

from . import views

app_name = "elipse"

urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("chat/", views.Chat.as_view(), name="chat"),
    path("sugerencias/", views.Sugerencias.as_view(), name="sugerencias"),
    path("autocompletar-falla/", views.AutocompletarFalla.as_view(), name="autocompletar_falla"),
]
