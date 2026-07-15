from django.contrib import admin

from . import models


@admin.register(models.Trabajador)
class TrabajadorAdmin(admin.ModelAdmin):
    list_display = ("numeroNomina", "nombre", "apellidoPat", "usuario", "correo", "rol", "actividad")
    list_filter = ("rol", "especialidad", "actividad")
    search_fields = ("numeroNomina", "nombre", "apellidoPat", "usuario", "correo")


admin.site.register(models.Rol)
admin.site.register(models.Especialidad)