from django.urls import path

from . import views

app_name = "elipse"

urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("chat/", views.Chat.as_view(), name="chat"),
]
