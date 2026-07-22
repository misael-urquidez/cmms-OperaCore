from django.urls import path
from . import views

app_name = "maquinaria"

urlpatterns = [
    path("ping/", views.PingAPIView.as_view(), name="ping"),
    # ------------ PLANTA ----------------------------------------------------
    path("v1/planta/list/", views.ListarPlantaAPIView.as_view(), name="list_plantas"),
    path("v1/planta/create/", views.CrearPlantaAPIView.as_view(), name="create_planta"),
    path("v1/planta/<str:codigo>/", views.DetailPlantaAPIView.as_view(), name="detail_planta"),
    path("v1/planta/update/<str:codigo>/", views.UpdatePlantaAPIView.as_view(), name="update_planta"),

    # ------------ AREA ------------------------------------------------------
    path("v1/area/list/", views.ListarAreaAPIView.as_view(), name="list_areas"),
    path("v1/area/create/", views.CrearAreaAPIView.as_view(), name="create_area"),
    path("v1/area/<str:codigo>/", views.DetailAreaAPIView.as_view(), name="detail_area"),
    path("v1/area/update/<str:codigo>/", views.UpdateAreaAPIView.as_view(), name="update_area"),

    # ------------ EDO MAQUINA -----------------------------------------------
    path("v1/edo_maquina/list/", views.ListarEdoMaquinaAPIView.as_view(), name="list_edos_maquina"),
    path("v1/edo_maquina/create/", views.CrearEdoMaquinaAPIView.as_view(), name="create_edo_maquina"),
    path("v1/edo_maquina/<str:codigo>/", views.DetailEdoMaquinaAPIView.as_view(), name="detail_edo_maquina"),
    path("v1/edo_maquina/update/<str:codigo>/", views.UpdateEdoMaquinaAPIView.as_view(), name="update_edo_maquina"),

    # ------------ LINEA -----------------------------------------------------
    path("v1/linea/list/", views.ListarLineaAPIView.as_view(), name="list_lineas"),
    path("v1/linea/create/", views.CrearLineaAPIView.as_view(), name="create_linea"),
    path("v1/linea/<str:codigo>/", views.DetailLineaAPIView.as_view(), name="detail_linea"),
    path("v1/linea/update/<str:codigo>/", views.UpdateLineaAPIView.as_view(), name="update_linea"),

    # ------------ MARCA -----------------------------------------------------
    path("v1/marca/list/", views.ListarMarcaAPIView.as_view(), name="list_marcas"),
    path("v1/marca/create/", views.CrearMarcaAPIView.as_view(), name="create_marca"),
    path("v1/marca/<str:clave>/", views.DetailMarcaAPIView.as_view(), name="detail_marca"), 
    path("v1/marca/update/<str:clave>/", views.UpdateMarcaAPIView.as_view(), name="update_marca"),

    # ------------ MODELO ----------------------------------------------------
    path("v1/modelo/list/", views.ListarModeloAPIView.as_view(), name="list_modelos"),
    path("v1/modelo/create/", views.CrearModeloAPIView.as_view(), name="create_modelo"),
    path("v1/modelo/<str:codigo>/", views.DetailModeloAPIView.as_view(), name="detail_modelo"),
    path("v1/modelo/update/<str:codigo>/", views.UpdateModeloAPIView.as_view(), name="update_modelo"),

    # ------------ TIPO MAQUINA ----------------------------------------------
    path("v1/tipo_maquina/list/", views.ListarTipoMaquinaAPIView.as_view(), name="list_tipos_maquina"),
    path("v1/tipo_maquina/create/", views.CrearTipoMaquinaAPIView.as_view(), name="create_tipo_maquina"),
    path("v1/tipo_maquina/<int:pk>/", views.DetailTipoMaquinaAPIView.as_view(), name="detail_tipo_maquina"),  
    path("v1/tipo_maquina/update/<int:pk>/", views.UpdateTipoMaquinaAPIView.as_view(), name="update_tipo_maquina"),

    # ------------ MAQUINA ---------------------------------------------------
    path("v1/maquina/list/", views.ListarMaquinaAPIView.as_view(), name="list_maquinas"),
    path("v1/maquina/create/", views.CrearMaquinaAPIView.as_view(), name="create_maquina"),
    path("v1/maquina/<str:codigo>/", views.DetailMaquinaAPIView.as_view(), name="detail_maquina"),
    path("v1/maquina/update/<str:codigo>/", views.UpdateMaquinaAPIView.as_view(), name="update_maquina"),
]
