from django.contrib import admin

from .models import (
    Clasificacion,
    EdoHerramienta,
    EdoRefaccion,
    EstadoHerramienta,
    EstadoRefaccion,
    Herramienta,
    Movimiento,
    Proveedor,
    Refaccion,
    TipoHerramienta,
    TipoRefaccion,
)


@admin.register(Refaccion)
class RefaccionAdmin(admin.ModelAdmin):
    list_display = ['numero_registro', 'nombre', 'codigo_sku', 'stock', 'stock_minimo', 'punto_reorden', 'stock_bajo']
    list_filter = ['tipo_refaccion', 'clasificacion', 'proveedor']
    search_fields = ['nombre', 'codigo_sku', 'codigo_inventario']


@admin.register(Herramienta)
class HerramientaAdmin(admin.ModelAdmin):
    list_display = ['numero_registro', 'nombre', 'tipo_herramienta']
    search_fields = ['nombre']


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ['numero_registro', 'tipo_movimiento', 'refaccion', 'fecha', 'hora', 'orden_mantenimiento']
    list_filter = ['tipo_movimiento', 'fecha']


admin.site.register(Proveedor)
admin.site.register(TipoRefaccion)
admin.site.register(Clasificacion)
admin.site.register(EdoRefaccion)
admin.site.register(TipoHerramienta)
admin.site.register(EdoHerramienta)
admin.site.register(EstadoRefaccion)
admin.site.register(EstadoHerramienta)
