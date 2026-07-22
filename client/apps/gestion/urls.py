from django.urls import path
from . import views

app_name = "gestion"

urlpatterns = [
    path("", views.GestionIndex.as_view(), name="index"),
    path("<slug:slug>/", views.GestionListView.as_view(), name="list"),
    path("<slug:slug>/crear/", views.GestionCreateView.as_view(), name="crear"),
    path("<slug:slug>/<str:pk>/editar/", views.GestionEditView.as_view(), name="editar"),
    path("<slug:slug>/<str:pk>/eliminar/", views.GestionDeleteView.as_view(), name="eliminar"),
]
