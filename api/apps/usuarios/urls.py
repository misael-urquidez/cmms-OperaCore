from django.urls import path
from . import views

app_name = "usuarios"

urlpatterns = [
    path("ping/", views.PingAPIView.as_view(), name="ping"),

    # v1 / v2 como en las clases de tu maestro, agrega aqui conforme crees
    # tus vistas de list/detail/create/update/delete:
    # path("v1/list/", views.ListUsuariosAPIView.as_view(), name="list"),
    # path("v1/<int:pk>/", views.DetailUsuariosAPIView.as_view(), name="detail"),
    # path("v2/create/", views.CreateUsuariosAPIView.as_view(), name="create"),
]
