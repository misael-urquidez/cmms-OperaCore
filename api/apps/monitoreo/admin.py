from django.contrib import admin

from .models import LecturaSensor


@admin.register(LecturaSensor)
class LecturaSensorAdmin(admin.ModelAdmin):
    list_display = ("numeroRegistro", "maquina", "timestamp", "origen", "vibracion", "golpe")
    list_filter = ("origen", "golpe")
    search_fields = ("maquina__codigo", "maquina__nombre")
    ordering = ("-timestamp",)
