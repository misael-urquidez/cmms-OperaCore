from django.urls import path
from . import views

app_name = "fallas"

urlpatterns = [
    path("ping/", views.PingAPIView.as_view(), name="ping"),

    # v1 / v2 como en las clases de tu maestro, agrega aqui conforme crees
    # tus vistas de list/detail/create/update/delete:
    # path("v1/list/", views.ListFallasAPIView.as_view(), name="list"),
    # path("v1/<int:pk>/", views.DetailFallasAPIView.as_view(), name="detail"),
    # path("v2/create/", views.CreateFallasAPIView.as_view(), name="create"),
]
