from django.urls import path
from . import views

app_name = "inventario"

urlpatterns = [
    # Ping
    path("ping/", views.PingAPIView.as_view(), name="ping"),

    # Catálogos agregados
    path("v1/catalogos/", views.CatalogosInventarioAPIView.as_view(), name="catalogos"),

    # ------------ REFACCIONES ------------
    path("v1/refacciones/list/", views.RefaccionListAPIView.as_view(), name="refacciones-list"),
    path("v1/refacciones/<int:pk>/", views.RefaccionDetailAPIView.as_view(), name="refacciones-detail"),
    path("v2/refacciones/create/", views.RefaccionCreateAPIView.as_view(), name="refacciones-create"),

    # ------------ PIEZAS ------------
    path("v1/piezas/list/", views.PiezaListAPIView.as_view(), name="piezas-list"),
    path("v1/piezas/<str:pk>/", views.PiezaDetailAPIView.as_view(), name="piezas-detail"),
    path("v2/piezas/create/", views.PiezaCreateAPIView.as_view(), name="piezas-create"),

    # ------------ HERRAMIENTAS ------------
    path("v1/herramientas/list/", views.HerramientaListAPIView.as_view(), name="herramientas-list"),
    path("v1/herramientas/<int:pk>/", views.HerramientaDetailAPIView.as_view(), name="herramientas-detail"),
    path("v2/herramientas/create/", views.HerramientaCreateAPIView.as_view(), name="herramientas-create"),

    # ------------ PROVEEDORES ------------
    path("v1/proveedores/list/", views.ProveedorListAPIView.as_view(), name="proveedores-list"),
    path("v1/proveedores/<str:pk>/", views.ProveedorDetailAPIView.as_view(), name="proveedores-detail"),
    path("v2/proveedores/create/", views.ProveedorCreateAPIView.as_view(), name="proveedores-create"),

    # ------------ CLASIFICACIONES ------------
    path("v1/clasificaciones/list/", views.ClasificacionListAPIView.as_view(), name="clasificaciones-list"),
    path("v1/clasificaciones/<str:pk>/", views.ClasificacionDetailAPIView.as_view(), name="clasificaciones-detail"),
    path("v2/clasificaciones/create/", views.ClasificacionCreateAPIView.as_view(), name="clasificaciones-create"),

    # ------------ ESTADOS ------------
    path("v1/estados-herramienta/list/", views.EdoHerramientaListAPIView.as_view(), name="estados-herramienta-list"),
    path("v1/estados-herramienta/<str:pk>/", views.EdoHerramientaDetailAPIView.as_view(), name="estados-herramienta-detail"),
    path("v2/estados-herramienta/create/", views.EdoHerramientaCreateAPIView.as_view(), name="estados-herramienta-create"),

    path("v1/estados-pieza/list/", views.EdoPiezaListAPIView.as_view(), name="estados-pieza-list"),
    path("v1/estados-pieza/<str:pk>/", views.EdoPiezaDetailAPIView.as_view(), name="estados-pieza-detail"),
    path("v2/estados-pieza/create/", views.EdoPiezaCreateAPIView.as_view(), name="estados-pieza-create"),

    path("v1/estados-refaccion/list/", views.EdoRefaccionListAPIView.as_view(), name="estados-refaccion-list"),
    path("v1/estados-refaccion/<str:pk>/", views.EdoRefaccionDetailAPIView.as_view(), name="estados-refaccion-detail"),
    path("v2/estados-refaccion/create/", views.EdoRefaccionCreateAPIView.as_view(), name="estados-refaccion-create"),

    # ------------ TIPOS ------------
    path("v1/tipos-herramienta/list/", views.TipoHerramientaListAPIView.as_view(), name="tipos-herramienta-list"),
    path("v1/tipos-herramienta/<int:pk>/", views.TipoHerramientaDetailAPIView.as_view(), name="tipos-herramienta-detail"),
    path("v2/tipos-herramienta/create/", views.TipoHerramientaCreateAPIView.as_view(), name="tipos-herramienta-create"),

    path("v1/tipos-pieza/list/", views.TipoPiezaListAPIView.as_view(), name="tipos-pieza-list"),
    path("v1/tipos-pieza/<int:pk>/", views.TipoPiezaDetailAPIView.as_view(), name="tipos-pieza-detail"),
    path("v2/tipos-pieza/create/", views.TipoPiezaCreateAPIView.as_view(), name="tipos-pieza-create"),

    path("v1/tipos-refaccion/list/", views.TipoRefaccionListAPIView.as_view(), name="tipos-refaccion-list"),
    path("v1/tipos-refaccion/<int:pk>/", views.TipoRefaccionDetailAPIView.as_view(), name="tipos-refaccion-detail"),
    path("v2/tipos-refaccion/create/", views.TipoRefaccionCreateAPIView.as_view(), name="tipos-refaccion-create"),

    # ------------ RELACIONES (llave compuesta) ------------
    path("v1/refacc-maqui/list/", views.RefaccMaquiListAPIView.as_view(), name="refacc-maqui-list"),
    path("v1/refacc-maqui/<str:maquina>/<int:refaccion>/", views.RefaccMaquiDetailAPIView.as_view(), name="refacc-maqui-detail"),
    path("v2/refacc-maqui/create/", views.RefaccMaquiCreateAPIView.as_view(), name="refacc-maqui-create"),

    path("v1/existencia-herramienta/list/", views.EstadoHerramientaListAPIView.as_view(), name="existencia-herramienta-list"),
    path("v1/existencia-herramienta/<int:herramienta>/<str:edo_herramienta>/", views.EstadoHerramientaDetailAPIView.as_view(), name="existencia-herramienta-detail"),
    path("v2/existencia-herramienta/create/", views.EstadoHerramientaCreateAPIView.as_view(), name="existencia-herramienta-create"),

    path("v1/existencia-refaccion/list/", views.EstadoRefaccionListAPIView.as_view(), name="existencia-refaccion-list"),
    path("v1/existencia-refaccion/<str:estado_refaccion>/<int:refaccion>/", views.EstadoRefaccionDetailAPIView.as_view(), name="existencia-refaccion-detail"),
    path("v2/existencia-refaccion/create/", views.EstadoRefaccionCreateAPIView.as_view(), name="existencia-refaccion-create"),
]