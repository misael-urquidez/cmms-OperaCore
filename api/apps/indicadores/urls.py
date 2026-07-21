from django.urls import path
from . import views

app_name = "indicadores"

urlpatterns = [
    path("ping/", views.PingAPIView.as_view(), name="ping"),
    # ------------ INDICADOR --------------------------------------------------------
    path("v1/indicador/list/", views.ListarIndicadorAPIView.as_view(), name="list_indicadores"),
    path("v1/indicador/create/", views.CrearIndicadorAPIView.as_view(), name="create_indicador"),
    path("v1/indicador/<int:pk>/", views.DetailIndicadorAPIView.as_view(), name="detail_indicador"),
    path("v1/indicador/update/<int:pk>/", views.UpdateIndicadorAPIView.as_view(), name="update_indicador"),
]