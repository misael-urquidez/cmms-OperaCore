from django.urls import path
from . import views

app_name = "maquinaria"

urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("lista/", views.ListarMaquinas.as_view(), name="list"),
    path("<str:codigo>/", views.DetalleMaquina.as_view(), name="detail"),
]