from django.urls import path
from . import views

app_name = "inventario"

urlpatterns = [
    # Dashboard / Index
    path("", views.Index.as_view(), name="index"),

    # ------------ REFACCIONES --------------------------------------------------
    path("refacciones/", views.ListaRefacciones.as_view(), name="lista_refacciones"),
    path("refacciones/crear/", views.CrearRefaccion.as_view(), name="crear_refaccion"),

    # ------------ PIEZAS -------------------------------------------------------
    path("piezas/", views.ListaPiezas.as_view(), name="lista_piezas"),
    path("piezas/crear/", views.CrearPieza.as_view(), name="crear_pieza"),

    # ------------ HERRAMIENTAS --------------------------------------------------
    path("herramientas/", views.ListaHerramientas.as_view(), name="lista_herramientas"),
    path("herramientas/crear/", views.CrearHerramienta.as_view(), name="crear_herramienta"),

    # ------------ PROVEEDORES --------------------------------------------------
    path("proveedores/", views.ListaProveedores.as_view(), name="lista_proveedores"),
    path("proveedores/crear/", views.CrearProveedor.as_view(), name="crear_proveedor"),

    # ------------ CLASIFICACIONES ----------------------------------------------
    path("clasificaciones/", views.ListaClasificaciones.as_view(), name="lista_clasificaciones"),
    path("clasificaciones/crear/", views.CrearClasificacion.as_view(), name="crear_clasificacion"),

    # ------------ ESTADOS ------------------------------------------------------
    path("estados-herramienta/", views.ListaEstadosHerramienta.as_view(), name="lista_estados_herramienta"),
    path("estados-herramienta/crear/", views.CrearEstadoHerramienta.as_view(), name="crear_estado_herramienta"),

    path("estados-pieza/", views.ListaEstadosPieza.as_view(), name="lista_estados_pieza"),
    path("estados-pieza/crear/", views.CrearEstadoPieza.as_view(), name="crear_estado_pieza"),

    path("estados-refaccion/", views.ListaEstadosRefaccion.as_view(), name="lista_estados_refaccion"),
    path("estados-refaccion/crear/", views.CrearEstadoRefaccion.as_view(), name="crear_estado_refaccion"),

    # ------------ TIPOS --------------------------------------------------------
    path("tipos-herramienta/", views.ListaTiposHerramienta.as_view(), name="lista_tipos_herramienta"),
    path("tipos-herramienta/crear/", views.CrearTipoHerramienta.as_view(), name="crear_tipo_herramienta"),

    path("tipos-pieza/", views.ListaTiposPieza.as_view(), name="lista_tipos_pieza"),
    path("tipos-pieza/crear/", views.CrearTipoPieza.as_view(), name="crear_tipo_pieza"),

    path("tipos-refaccion/", views.ListaTiposRefaccion.as_view(), name="lista_tipos_refaccion"),
    path("tipos-refaccion/crear/", views.CrearTipoRefaccion.as_view(), name="crear_tipo_refaccion"),
]