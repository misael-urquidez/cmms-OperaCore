from django.urls import path

from . import views

app_name = "usuarios"

urlpatterns = [
    path("", views.AuthView.as_view(), name="index"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("registro/", views.RegistroView.as_view(), name="registro"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
]