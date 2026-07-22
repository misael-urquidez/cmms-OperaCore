"""
URL configuration - OperaCore Client.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", TemplateView.as_view(template_name="home.html"), name="home"),

    path("usuarios/", include("apps.usuarios.urls")),
    path("maquinaria/", include("apps.maquinaria.urls")),
    path("mantenimiento/", include("apps.mantenimiento.urls")),
    path("fallas/", include("apps.fallas.urls")),
    path("inventario/", include("apps.inventario.urls")),
    path("indicadores/", include("apps.indicadores.urls")),
    path("elipse/", include("apps.elipse.urls")),
    path("monitoreo/", include("apps.monitoreo.urls")),
    path("gestion/", include("apps.gestion.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
