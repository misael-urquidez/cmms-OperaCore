from django.contrib import admin

from .models import Refaccion, Herramienta, Proveedor

admin.site.register(Refaccion)
admin.site.register(Herramienta)
admin.site.register(Proveedor)