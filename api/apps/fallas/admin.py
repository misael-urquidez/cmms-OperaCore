from django.contrib import admin

from . import models


@admin.register(models.ReporteFalla)
class ReporteFallaAdmin(admin.ModelAdmin):
    list_display = (
        "numeroRegistro", "asunto", "fechaCreacion", "horaCreacion",
        "maquina", "trabajador", "tipo_falla", "tipo_severidad",
    )
    list_filter = ("tipo_severidad", "tipo_falla", "fechaCreacion")
    search_fields = ("asunto", "causaRaiz", "descripcion")


@admin.register(models.TipoSeveridad)
class TipoSeveridadAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre")


@admin.register(models.TipoFalla)
class TipoFallaAdmin(admin.ModelAdmin):
    list_display = ("numeroRegistro", "nombre")


@admin.register(models.EstadoReporte)
class EstadoReporteAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre")


admin.site.register(models.Maquina)
admin.site.register(models.TipoReporte)
