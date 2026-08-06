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

    # ------------ MOVIMIENTO ------------
    path("v1/movimientos/list/", views.MovimientoListAPIView.as_view(), name="movimientos-list"),
    path("v2/movimientos/create/", views.MovimientoCreateAPIView.as_view(), name="movimientos-create"),

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
    # ------------ REPORTE_FALLA (disponibles para adjuntar) ------------
    path("v1/reportes-disponibles/list/", views.ReporteFallaDisponibleListAPIView.as_view(), name="reportes-disponibles-list"),

    path("v1/ordenes/list/", views.OrdenMantenimientoListAPIView.as_view(), name="ordenes-list"),
    path("v1/ordenes/<str:folio>/", views.OrdenMantenimientoDetailAPIView.as_view(), name="ordenes-detail"),
    path("v2/ordenes/create/", views.OrdenMantenimientoCreateAPIView.as_view(), name="ordenes-create"),
    path("v2/ordenes/<str:folio>/asignar/", views.OrdenMantenimientoAsignarAPIView.as_view(), name="ordenes-asignar"),
    path("v2/ordenes/<str:folio>/iniciar/", views.OrdenMantenimientoIniciarAPIView.as_view(), name="ordenes-iniciar"),
    path("v2/ordenes/<str:folio>/cerrar/", views.OrdenMantenimientoCerrarAPIView.as_view(), name="ordenes-cerrar"),
    path("v2/ordenes/<str:folio>/update/", views.OrdenMantenimientoUpdateAPIView.as_view(), name="ordenes-update"),
    path("v2/ordenes/<str:folio>/cancelar/", views.OrdenMantenimientoCancelarAPIView.as_view(), name="ordenes-cancelar"),
    # exportaciones
    path("v1/ordenes/<str:folio>/export/csv/", views.ExportarOrdenCSVAPIView.as_view(), name="ordenes-export-csv"),
    path("v1/ordenes/<str:folio>/export/xlsx/", views.ExportarOrdenXLSXAPIView.as_view(), name="ordenes-export-xlsx"),
    path("v1/ordenes/<str:folio>/export/pdf/", views.ExportarOrdenPDFAPIView.as_view(), name="ordenes-export-pdf"),
]
