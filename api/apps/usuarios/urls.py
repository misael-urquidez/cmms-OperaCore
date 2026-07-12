from django.urls import path

from . import views

app_name = "usuarios"

urlpatterns = [
    path("ping/", views.PingAPIView.as_view(), name="ping"),
    path("roles/", views.RolListAPIView.as_view(), name="roles"),
    path("especialidades/", views.EspecialidadListAPIView.as_view(), name="especialidades"),
    path("registro/", views.RegistroAPIView.as_view(), name="registro"),
    path("login/", views.LoginAPIView.as_view(), name="login"),
]