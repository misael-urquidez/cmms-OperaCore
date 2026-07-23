"""
URL configuration - OperaCore API.
"""

from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", obtain_auth_token, name="login"),

    path("api/usuarios/", include("apps.usuarios.urls")),
    path("api/maquinaria/", include("apps.maquinaria.urls")),
    path("api/mantenimiento/", include("apps.mantenimiento.urls")),
    path("api/fallas/", include("apps.fallas.urls")),
    path("api/inventario/", include("apps.inventario.urls")),
    path("api/indicadores/", include("apps.indicadores.urls")),
    path("api/elipse/", include("apps.elipse.urls")),
    path("api/monitoreo/", include("apps.monitoreo.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)