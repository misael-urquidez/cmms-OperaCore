import requests
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views import View, generic

API_URL = f"{settings.API_BASE_URL}/indicadores"

# Sesion HTTP a nivel de modulo: reusa la conexion TCP con el api/.
SESSION = requests.Session()

# El ping es solo un status, no data real: cache de 30 seg para no
# pegarle al api/ en cada click al modulo.
PING_TTL = 30

# Mismo whitelist que apps/indicadores/views.py del api/ (VISTAS_KPI): se
# repite aqui solo para poder devolver 404 sin tener que pegarle al api si
# alguien manda una <vista> que no existe.
VISTAS_KPI = {
    "estado-flota", "reportes-atencion", "stock", "fallas-por-maquina",
    "top-fallas", "horas-operacion", "mantenimiento-por-maquina",
    "indicadores-actuales", "disponibilidad-linea", "monitoreo-predictivo",
}


class Index(generic.View):
    """Pantalla principal del modulo Indicadores. Consume el api/ por HTTP."""

    template_name = "indicadores/index.html"

    def get(self, request):
        usuario = request.session.get("usuario")
        if not usuario:
            messages.warning(request, "Inicia sesión para continuar.")
            return redirect("usuarios:index")
        response = cache.get("indicadores_ping")
        if response is None:
            try:
                response = SESSION.get(f"{API_URL}/ping/", timeout=5).json()
            except requests.exceptions.RequestException:
                response = {"status": "sin conexion con el api"}
            cache.set("indicadores_ping", response, PING_TTL)
        return render(request, self.template_name, {
            "modulo": "Indicadores", "api_status": response,
            "seccion": "indicadores", "subseccion": "panel",
        })


class KPIsPage(generic.View):
    """Submodulo 'KPI's': las 10 vistas de vistas_kpi.sql, cada una en su
    propia tabla generica (sin mapeo de columnas a mano). El JS arma las
    columnas dinamicamente a partir de las keys que regrese cada vista."""

    template_name = "indicadores/kpis.html"

    def get(self, request):
        usuario = request.session.get("usuario")
        if not usuario:
            messages.warning(request, "Inicia sesión para continuar.")
            return redirect("usuarios:index")
        return render(request, self.template_name, {
            "seccion": "indicadores", "subseccion": "kpis",
        })


class KPIVistaProxy(View):
    """Reenvia GET /indicadores/v1/kpi/<vista>/ al api/, tal cual, para que
    el JS del navegador pueda pedirlo con fetch() en mismo origen (sin
    CORS) y con la sesion del usuario ya validada."""

    def get(self, request, vista):
        if vista not in VISTAS_KPI:
            return JsonResponse(
                {"detail": "Vista no encontrada.", "disponibles": sorted(VISTAS_KPI)}, status=404,
            )
        try:
            respuesta = SESSION.get(f"{API_URL}/v1/kpi/{vista}/", timeout=8)
            respuesta.raise_for_status()
        except requests.RequestException:
            return JsonResponse({"detail": "No fue posible conectar con el API."}, status=502)
        return JsonResponse(respuesta.json(), safe=False)


class ResumenProxy(View):
    """Reenvia GET /indicadores/v1/resumen/ al api/."""

    def get(self, request):
        try:
            respuesta = SESSION.get(f"{API_URL}/v1/resumen/", timeout=8)
            respuesta.raise_for_status()
        except requests.RequestException:
            return JsonResponse({"detail": "No fue posible conectar con el API."}, status=502)
        return JsonResponse(respuesta.json(), safe=False)


class ReporteKPIExportProxy(View):
    """Reenvia GET /indicadores/v1/reporte/export/<formato>/ al api/.
    El navegador descarga el archivo directamente gracias a Content-Disposition."""

    def get(self, request, formato):
        try:
            respuesta = SESSION.get(f"{API_URL}/v1/reporte/export/{formato}/", params=request.GET, timeout=30)
            respuesta.raise_for_status()
        except requests.RequestException:
            return JsonResponse({"detail": "No fue posible conectar con el API."}, status=502)

        response = HttpResponse(respuesta.content, content_type=respuesta.headers["Content-Type"])
        response["Content-Disposition"] = respuesta.headers["Content-Disposition"]
        return response


# A partir de aqui sigue el patron de tu maestro (home/views.py):
# cada vista pega a un endpoint del api/ con requests.get/post/put/delete
# y le pasa la respuesta (.json()) al template via el contexto. Ejemplo:
#
# class ListarAlgo(generic.View):
#     template_name = "indicadores/list.html"
#
#     def get(self, request):
#         data = requests.get(f"{API_URL}/v1/list/").json()
#         return render(request, self.template_name, {"items": data})
#
# class CrearAlgo(generic.View):
#     template_name = "indicadores/create.html"
#
#     def get(self, request):
#         return render(request, self.template_name, {})
#
#     def post(self, request):
#         payload = {"campo": request.POST.get("campo")}
#         requests.post(f"{API_URL}/v2/create/", json=payload)
#         return redirect("indicadores:index")