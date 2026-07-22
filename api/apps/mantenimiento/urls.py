from django.urls import path
from . import views

app_name = "mantenimiento"

urlpatterns = [
    path("ping/", views.PingAPIView.as_view(), name="ping"),

    # ------------ ESTADO_ORDEN ------------
    path("v1/estado-orden/list/", views.EstadoOrdenListAPIView.as_view(), name="estado-orden-list"),
    path("v2/estado-orden/create/", views.EstadoOrdenCreateAPIView.as_view(), name="estado-orden-create"),
    path("v1/estado-orden/<str:codigo>/", views.EstadoOrdenDetailAPIView.as_view(), name="estado-orden-detail"),

    # ------------ TIPO_MANTENIMIENTO ------------
    path("v1/tipo-mantenimiento/list/", views.TipoMantenimientoListAPIView.as_view(), name="tipo-mantenimiento-list"),
    path("v2/tipo-mantenimiento/create/", views.TipoMantenimientoCreateAPIView.as_view(), name="tipo-mantenimiento-create"),
    path("v1/tipo-mantenimiento/<str:codigo>/", views.TipoMantenimientoDetailAPIView.as_view(), name="tipo-mantenimiento-detail"),

    # ------------ TAREAS ------------
    path("v1/tareas/list/", views.TareasListAPIView.as_view(), name="tareas-list"),
    path("v2/tareas/create/", views.TareasCreateAPIView.as_view(), name="tareas-create"),
    path("v1/tareas/<int:numeroregistro>/", views.TareasDetailAPIView.as_view(), name="tareas-detail"),

    # ------------ TIPO_MOVIMIENTO ------------
    path("v1/tipo-movimiento/list/", views.TipoMovimientoListAPIView.as_view(), name="tipo-movimiento-list"),
    path("v2/tipo-movimiento/create/", views.TipoMovimientoCreateAPIView.as_view(), name="tipo-movimiento-create"),
    path("v1/tipo-movimiento/<str:codigo>/", views.TipoMovimientoDetailAPIView.as_view(), name="tipo-movimiento-detail"),

    # ------------ TAREA_ORDEN (llave compuesta) ------------
    path("v1/tarea-orden/list/", views.TareaOrdenListAPIView.as_view(), name="tarea-orden-list"),
    path("v2/tarea-orden/create/", views.TareaOrdenCreateAPIView.as_view(), name="tarea-orden-create"),
    path("v1/tarea-orden/<int:tarea>/<str:orden_mantenimiento>/", views.TareaOrdenDetailAPIView.as_view(), name="tarea-orden-detail"),

    # ------------ HERRA_ORDEN (llave compuesta) ------------
    path("v1/herra-orden/list/", views.HerraOrdenListAPIView.as_view(), name="herra-orden-list"),
    path("v2/herra-orden/create/", views.HerraOrdenCreateAPIView.as_view(), name="herra-orden-create"),
    path("v1/herra-orden/<int:herramienta>/<str:orden_mantenimiento>/", views.HerraOrdenDetailAPIView.as_view(), name="herra-orden-detail"),

    # ------------ TRABA_ORDE_PERSONAL (llave compuesta) ------------
    path("v1/traba-orden-personal/list/", views.TrabaOrdePersonalListAPIView.as_view(), name="traba-orden-personal-list"),
    path("v2/traba-orden-personal/create/", views.TrabaOrdePersonalCreateAPIView.as_view(), name="traba-orden-personal-create"),
    path("v1/traba-orden-personal/<str:trabajador>/<str:orden_mantenimiento>/", views.TrabaOrdePersonalDetailAPIView.as_view(), name="traba-orden-personal-detail"),
]
