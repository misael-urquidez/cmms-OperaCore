from django.urls import path
from . import views

app_name = "notificaciones"

urlpatterns = [
    path("list/", views.NotificacionesListAPIView.as_view(), name="notificaciones-list"),
]
