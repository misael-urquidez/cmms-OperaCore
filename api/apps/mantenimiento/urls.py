from django.urls import path
from . import views

app_name = "mantenimiento"

urlpatterns = [
    path("ping/", views.PingAPIView.as_view(), name="ping"),
    # ------------ ESTADO ORDEN -----------------------------------------------------
    path("v1/estado_orden/list/", views.ListarEstadoOrdenAPIView.as_view(), name="list_estados_orden"),
    path("v1/estado_orden/create/", views.CrearEstadoOrdenAPIView.as_view(), name="create_estado_orden"),
    path("v1/estado_orden/<str:codigo>/", views.DetailEstadoOrdenAPIView.as_view(), name="detail_estado_orden"),
    path("v1/estado_orden/update/<str:codigo>/", views.UpdateEstadoOrdenAPIView.as_view(), name="update_estado_orden"),

    # ------------ TIPO MANTENIMIENTO -----------------------------------------------
    path("v1/tipo_mantenimiento/list/", views.ListarTipoMantenimientoAPIView.as_view(), name="list_tipos_mantenimiento"),
    path("v1/tipo_mantenimiento/create/", views.CrearTipoMantenimientoAPIView.as_view(), name="create_tipo_mantenimiento"),
    path("v1/tipo_mantenimiento/<str:codigo>/", views.DetailTipoMantenimientoAPIView.as_view(), name="detail_tipo_mantenimiento"),
    path("v1/tipo_mantenimiento/update/<str:codigo>/", views.UpdateTipoMantenimientoAPIView.as_view(), name="update_tipo_mantenimiento"),

    # ------------ TAREAS -----------------------------------------------------------
    path("v1/tareas/list/", views.ListarTareasAPIView.as_view(), name="list_tareas"),
    path("v1/tareas/create/", views.CrearTareasAPIView.as_view(), name="create_tarea"),
    path("v1/tareas/<int:pk>/", views.DetailTareasAPIView.as_view(), name="detail_tarea"),
    path("v1/tareas/update/<int:pk>/", views.UpdateTareasAPIView.as_view(), name="update_tarea"),

    # ------------ TIPO MOVIMIENTO --------------------------------------------------
    path("v1/tipo_movimiento/list/", views.ListarTipoMovimientoAPIView.as_view(), name="list_tipos_movimiento"),
    path("v1/tipo_movimiento/create/", views.CrearTipoMovimientoAPIView.as_view(), name="create_tipo_movimiento"),
    path("v1/tipo_movimiento/<str:codigo>/", views.DetailTipoMovimientoAPIView.as_view(), name="detail_tipo_movimiento"),
    path("v1/tipo_movimiento/update/<str:codigo>/", views.UpdateTipoMovimientoAPIView.as_view(), name="update_tipo_movimiento"),

    # ------------ ORDEN MANTENIMIENTO ----------------------------------------------
    path("v1/orden_mantenimiento/list/", views.ListarOrdenMantenimientoAPIView.as_view(), name="list_ordenes_mantenimiento"),
    path("v1/orden_mantenimiento/create/", views.CrearOrdenMantenimientoAPIView.as_view(), name="create_orden_mantenimiento"),
    path("v1/orden_mantenimiento/<str:folio>/", views.DetailOrdenMantenimientoAPIView.as_view(), name="detail_orden_mantenimiento"),
    path("v1/orden_mantenimiento/update/<str:folio>/", views.UpdateOrdenMantenimientoAPIView.as_view(), name="update_orden_mantenimiento"),

    # ------------ MOVIMIENTO -------------------------------------------------------
    path("v1/movimiento/list/", views.ListarMovimientoAPIView.as_view(), name="list_movimientos"),
    path("v1/movimiento/create/", views.CrearMovimientoAPIView.as_view(), name="create_movimiento"),
    path("v1/movimiento/<int:pk>/", views.DetailMovimientoAPIView.as_view(), name="detail_movimiento"),
    path("v1/movimiento/update/<int:pk>/", views.UpdateMovimientoAPIView.as_view(), name="update_movimiento"),

    # ------------ TABLAS DE RELACION / INTERMEDIAS ---------------------------------
    path("v1/tarea_orden/list/", views.ListarTareaOrdenAPIView.as_view(), name="list_tarea_orden"),
    path("v1/tarea_orden/create/", views.CrearTareaOrdenAPIView.as_view(), name="create_tarea_orden"),
    path("v1/tarea_orden/<int:tarea>/", views.DetailTareaOrdenAPIView.as_view(), name="detail_tarea_orden"),
    path("v1/tarea_orden/update/<int:tarea>/", views.UpdateTareaOrdenAPIView.as_view(), name="update_tarea_orden"),

    path("v1/herra_orden/list/", views.ListarHerraOrdenAPIView.as_view(), name="list_herra_orden"),
    path("v1/herra_orden/create/", views.CrearHerraOrdenAPIView.as_view(), name="create_herra_orden"),
    path("v1/herra_orden/<int:herramienta>/", views.DetailHerraOrdenAPIView.as_view(), name="detail_herra_orden"),
    path("v1/herra_orden/update/<int:herramienta>/", views.UpdateHerraOrdenAPIView.as_view(), name="update_herra_orden"),

    path("v1/traba_orde_personal/list/", views.ListarTrabaOrdePersonalAPIView.as_view(), name="list_traba_orde_personal"),
    path("v1/traba_orde_personal/create/", views.CrearTrabaOrdePersonalAPIView.as_view(), name="create_traba_orde_personal"),
    path("v1/traba_orde_personal/<str:trabajador>/", views.DetailTrabaOrdePersonalAPIView.as_view(), name="detail_traba_orde_personal"),
    path("v1/traba_orde_personal/update/<str:trabajador>/", views.UpdateTrabaOrdePersonalAPIView.as_view(), name="update_traba_orde_personal"),
]
