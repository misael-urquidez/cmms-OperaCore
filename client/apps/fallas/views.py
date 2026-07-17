import requests
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.views import generic

API_URL = f"{settings.API_BASE_URL}/fallas"

CATALOGOS_TTL = 60 * 10


def _cargar_catalogos():
    """Devuelve (severidades, tipos_falla, ok). Los toma del cache si estan;
    si no, los pide al api/ y los guarda. ok=False si el api/ no respondio."""
    severidades = cache.get("fallas_severidades")
    tipos_falla = cache.get("fallas_tipos_falla")
    if severidades is not None and tipos_falla is not None:
        return severidades, tipos_falla, True

    try:
        severidades = requests.get(f"{API_URL}/v1/tipos-severidad/", timeout=5).json()
        tipos_falla = requests.get(f"{API_URL}/v1/tipos-falla/", timeout=5).json()
    except requests.exceptions.RequestException:
        return [], [], False

    cache.set("fallas_severidades", severidades, CATALOGOS_TTL)
    cache.set("fallas_tipos_falla", tipos_falla, CATALOGOS_TTL)
    return severidades, tipos_falla, True


class ReporteFallaView(generic.View):
    """Formulario para crear un reporte de falla. GET carga los catalogos,
    POST envia el reporte al api/."""

    template_name = "fallas/reporte_falla.html"

    def get(self, request):
        severidades, tipos_falla, ok = _cargar_catalogos()
        if not ok:
            messages.warning(request, "No se pudieron cargar los catalogos (esta corriendo el api/?).")
        return render(request, self.template_name, {
            "severidades": severidades,
            "tipos_falla": tipos_falla,
        })

    def post(self, request):
        payload = {
            "asunto": request.POST.get("asunto", "").strip(),
            "descripcion": request.POST.get("descripcion", "").strip() or None,
            "causaRaiz": request.POST.get("causaRaiz", "").strip(),
            "tiempoParo": request.POST.get("tiempoParo") or None,
            "maquina": request.POST.get("maquina") or None,
            "tipo_falla": request.POST.get("tipo_falla") or None,
            "tipo_severidad": request.POST.get("tipo_severidad") or None,
        }

        try:
            response = requests.post(f"{API_URL}/v2/reportes/create/", json=payload, timeout=5)
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el servidor. Intenta mas tarde.")
            return redirect("fallas:reporte")

        if response.status_code == 201:
            messages.success(request, "Reporte de falla creado exitosamente.")
            return redirect("fallas:lista")

        try:
            errores = response.json()
        except ValueError:
            errores = {"error": "No se pudo crear el reporte."}

        for campo, detalle in errores.items():
            detalle_txt = detalle[0] if isinstance(detalle, list) else detalle
            messages.error(request, f"{campo}: {detalle_txt}")
        return redirect("fallas:reporte")


class ListaReportesView(generic.View):
    """Lista de reportes de falla."""

    template_name = "fallas/lista_reportes.html"

    def get(self, request):
        try:
            reportes = requests.get(f"{API_URL}/v1/reportes/list/", timeout=5).json()
        except requests.exceptions.RequestException:
            reportes = []
            messages.warning(request, "No se pudieron cargar los reportes (esta corriendo el api/?).")
        return render(request, self.template_name, {"reportes": reportes})
