from django.urls import path
from . import views

app_name = "inventario"

urlpatterns = [
    path("ping/", views.PingAPIView.as_view(), name="ping"),
    # ------------ CLASIFICACION ----------------------------------------------------
    path("v1/clasificacion/list/", views.ListarClasificacionAPIView.as_view(), name="list_clasificaciones"),
    path("v1/clasificacion/create/", views.CrearClasificacionAPIView.as_view(), name="create_clasificacion"),
    path("v1/clasificacion/<str:codigo>/", views.DetailClasificacionAPIView.as_view(), name="detail_clasificacion"),
    path("v1/clasificacion/update/<str:codigo>/", views.UpdateClasificacionAPIView.as_view(), name="update_clasificacion"),

    # ------------ EDO HERRAMIENTA --------------------------------------------------
    path("v1/edo_herramienta/list/", views.ListarEdoHerramientaAPIView.as_view(), name="list_edos_herramienta"),
    path("v1/edo_herramienta/create/", views.CrearEdoHerramientaAPIView.as_view(), name="create_edo_herramienta"),
    path("v1/edo_herramienta/<str:codigo>/", views.DetailEdoHerramientaAPIView.as_view(), name="detail_edo_herramienta"),
    path("v1/edo_herramienta/update/<str:codigo>/", views.UpdateEdoHerramientaAPIView.as_view(), name="update_edo_herramienta"),

    # ------------ EDO PIEZA --------------------------------------------------------
    path("v1/edo_pieza/list/", views.ListarEdoPiezaAPIView.as_view(), name="list_edos_pieza"),
    path("v1/edo_pieza/create/", views.CrearEdoPiezaAPIView.as_view(), name="create_edo_pieza"),
    path("v1/edo_pieza/<str:codigo>/", views.DetailEdoPiezaAPIView.as_view(), name="detail_edo_pieza"),
    path("v1/edo_pieza/update/<str:codigo>/", views.UpdateEdoPiezaAPIView.as_view(), name="update_edo_pieza"),

    # ------------ EDO REFACCION ----------------------------------------------------
    path("v1/edo_refaccion/list/", views.ListarEdoRefaccionAPIView.as_view(), name="list_edos_refaccion"),
    path("v1/edo_refaccion/create/", views.CrearEdoRefaccionAPIView.as_view(), name="create_edo_refaccion"),
    path("v1/edo_refaccion/<str:codigo>/", views.DetailEdoRefaccionAPIView.as_view(), name="detail_edo_refaccion"),
    path("v1/edo_refaccion/update/<str:codigo>/", views.UpdateEdoRefaccionAPIView.as_view(), name="update_edo_refaccion"),

    # ------------ TIPO HERRAMIENTA --------------------------------------------------
    path("v1/tipo_herramienta/list/", views.ListarTipoHerramientaAPIView.as_view(), name="list_tipos_herramienta"),
    path("v1/tipo_herramienta/create/", views.CrearTipoHerramientaAPIView.as_view(), name="create_tipo_herramienta"),
    path("v1/tipo_herramienta/<int:pk>/", views.DetailTipoHerramientaAPIView.as_view(), name="detail_tipo_herramienta"),
    path("v1/tipo_herramienta/update/<int:pk>/", views.UpdateTipoHerramientaAPIView.as_view(), name="update_tipo_herramienta"),

    # ------------ TIPO PIEZA --------------------------------------------------------
    path("v1/tipo_pieza/list/", views.ListarTipoPiezaAPIView.as_view(), name="list_tipos_pieza"),
    path("v1/tipo_pieza/create/", views.CrearTipoPiezaAPIView.as_view(), name="create_tipo_pieza"),
    path("v1/tipo_pieza/<int:pk>/", views.DetailTipoPiezaAPIView.as_view(), name="detail_tipo_pieza"),
    path("v1/tipo_pieza/update/<int:pk>/", views.UpdateTipoPiezaAPIView.as_view(), name="update_tipo_pieza"),

    # ------------ TIPO REFACCION ----------------------------------------------------
    path("v1/tipo_refaccion/list/", views.ListarTipoRefaccionAPIView.as_view(), name="list_tipos_refaccion"),
    path("v1/tipo_refaccion/create/", views.CrearTipoRefaccionAPIView.as_view(), name="create_tipo_refaccion"),
    path("v1/tipo_refaccion/<int:pk>/", views.DetailTipoRefaccionAPIView.as_view(), name="detail_tipo_refaccion"),
    path("v1/tipo_refaccion/update/<int:pk>/", views.UpdateTipoRefaccionAPIView.as_view(), name="update_tipo_refaccion"),

    # ------------ PROVEEDOR --------------------------------------------------------
    path("v1/proveedor/list/", views.ListarProveedorAPIView.as_view(), name="list_proveedores"),
    path("v1/proveedor/create/", views.CrearProveedorAPIView.as_view(), name="create_proveedor"),
    path("v1/proveedor/<str:codigo>/", views.DetailProveedorAPIView.as_view(), name="detail_proveedor"),
    path("v1/proveedor/update/<str:codigo>/", views.UpdateProveedorAPIView.as_view(), name="update_proveedor"),

    # ------------ HERRAMIENTA -------------------------------------------------------
    path("v1/herramienta/list/", views.ListarHerramientaAPIView.as_view(), name="list_herramientas"),
    path("v1/herramienta/create/", views.CrearHerramientaAPIView.as_view(), name="create_herramienta"),
    path("v1/herramienta/<int:pk>/", views.DetailHerramientaAPIView.as_view(), name="detail_herramienta"),
    path("v1/herramienta/update/<int:pk>/", views.UpdateHerramientaAPIView.as_view(), name="update_herramienta"),

    # ------------ PIEZA ------------------------------------------------------------
    path("v1/pieza/list/", views.ListarPiezaAPIView.as_view(), name="list_piezas"),
    path("v1/pieza/create/", views.CrearPiezaAPIView.as_view(), name="create_pieza"),
    path("v1/pieza/<str:numeroserie>/", views.DetailPiezaAPIView.as_view(), name="detail_pieza"),
    path("v1/pieza/update/<str:numeroserie>/", views.UpdatePiezaAPIView.as_view(), name="update_pieza"),

    # ------------ REFACCION --------------------------------------------------------
    path("v1/refaccion/list/", views.ListarRefaccionAPIView.as_view(), name="list_refacciones"),
    path("v1/refaccion/create/", views.CrearRefaccionAPIView.as_view(), name="create_refaccion"),
    path("v1/refaccion/<int:pk>/", views.DetailRefaccionAPIView.as_view(), name="detail_refaccion"),
    path("v1/refaccion/update/<int:pk>/", views.UpdateRefaccionAPIView.as_view(), name="update_refaccion"),

    # ------------ TABLAS DE RELACION / INTERMEDIAS ---------------------------------
    path("v1/refacc_maqui/list/", views.ListarRefaccMaquiAPIView.as_view(), name="list_refacc_maqui"),
    path("v1/refacc_maqui/create/", views.CrearRefaccMaquiAPIView.as_view(), name="create_refacc_maqui"),
    path("v1/refacc_maqui/<str:maquina>/", views.DetailRefaccMaquiAPIView.as_view(), name="detail_refacc_maqui"),
    path("v1/refacc_maqui/update/<str:maquina>/", views.UpdateRefaccMaquiAPIView.as_view(), name="update_refacc_maqui"),

    path("v1/estado_herramienta/list/", views.ListarEstadoHerramientaAPIView.as_view(), name="list_estado_herramienta"),
    path("v1/estado_herramienta/create/", views.CrearEstadoHerramientaAPIView.as_view(), name="create_estado_herramienta"),
    path("v1/estado_herramienta/<int:herramienta>/", views.DetailEstadoHerramientaAPIView.as_view(), name="detail_estado_herramienta"),
    path("v1/estado_herramienta/update/<int:herramienta>/", views.UpdateEstadoHerramientaAPIView.as_view(), name="update_estado_herramienta"),

    path("v1/estado_refaccion/list/", views.ListarEstadoRefaccionAPIView.as_view(), name="list_estado_refaccion"),
    path("v1/estado_refaccion/create/", views.CrearEstadoRefaccionAPIView.as_view(), name="create_estado_refaccion"),
    path("v1/estado_refaccion/<str:estado_refaccion>/", views.DetailEstadoRefaccionAPIView.as_view(), name="detail_estado_refaccion"),
    path("v1/estado_refaccion/update/<str:estado_refaccion>/", views.UpdateEstadoRefaccionAPIView.as_view(), name="update_estado_refaccion"),
]
