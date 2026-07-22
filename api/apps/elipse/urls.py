from django.urls import path

from . import views

app_name = "elipse"

urlpatterns = [
    path("chat/", views.ElipseChatAPIView.as_view(), name="chat"),
]
