from django.urls import path

from . import views

app_name = "usuarios"

urlpatterns = [
    path("ping/", views.PingAPIView.as_view(), name="ping"),
    path("roles/", views.RolListAPIView.as_view(), name="roles"),
    path("roles/create/", views.RolCreateAPIView.as_view(), name="roles-create"),
    path("roles/<str:codigo>/", views.RolDetailAPIView.as_view(), name="roles-detail"),
    path("especialidades/", views.EspecialidadListAPIView.as_view(), name="especialidades"),
    path("especialidades/create/", views.EspecialidadCreateAPIView.as_view(), name="especialidades-create"),
    path("especialidades/<int:numeroRegistro>/", views.EspecialidadDetailAPIView.as_view(), name="especialidades-detail"),
    path("v1/trabajadores/list/", views.TrabajadorListAPIView.as_view(), name="trabajadores-list"),
    path("v1/trabajadores/<str:numeroNomina>/", views.TrabajadorDetailAPIView.as_view(), name="trabajadores-detail"),
    path("registro/", views.RegistroAPIView.as_view(), name="registro"),
    path("login/", views.LoginAPIView.as_view(), name="login"),
]