from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import generic
from django.contrib import messages
import requests

from django.conf import settings
from django.core.cache import cache


API_URL = f"{settings.API_BASE_URL}/fallas"

# Sesion HTTP a nivel de modulo: se crea una vez y reusa la conexion TCP
# con el api/ en vez de abrir una nueva por cada request (menos latencia).
SESSION = requests.Session()

# Severidad, tipo de falla y estados casi no cambian: cache de 2 min.
# Maquinas se da de alta más seguido, asi que su cache es mucho mas corto
# (30 seg) para que una maquina nueva aparezca casi al instante.
# La lista de reportes cambia seguido pero no necesitas verla al segundo:
# 15 seg. El dashboard de usuarios comparte este mismo cache.
CATALOGOS_TTL = 60 * 2
MAQUINAS_TTL = 30
REPORTES_TTL = 15


def _cargar_catalogos():
    """Devuelve (severidades, tipos_falla, maquinas, estados, trabajadores, ok).
    Los toma del cache si estan todos; si falta alguno, pide todos juntos en
    UNA sola llamada al endpoint agregador del api/ y los vuelve a cachear
    cada uno con su propio TTL."""
    severidades = cache.get("fallas_severidades")
    tipos_falla = cache.get("fallas_tipos_falla")
    maquinas = cache.get("fallas_maquinas")
    estados = cache.get("fallas_estados")
    trabajadores = cache.get("fallas_trabajadores")

    if None not in (severidades, tipos_falla, maquinas, estados, trabajadores):
        return severidades, tipos_falla, maquinas, estados, trabajadores, True

    try:
        data = SESSION.get(f"{API_URL}/v1/catalogos-reporte/", timeout=5).json()
    except requests.exceptions.RequestException:
        return [], [], [], [], [], False

    severidades = data["severidades"]
    tipos_falla = data["tipos_falla"]
    maquinas = data["maquinas"]
    estados = data["estados"]
    trabajadores = data.get("trabajadores", [])

    cache.set("fallas_severidades", severidades, CATALOGOS_TTL)
    cache.set("fallas_tipos_falla", tipos_falla, CATALOGOS_TTL)
    cache.set("fallas_maquinas", maquinas, MAQUINAS_TTL)
    cache.set("fallas_estados", estados, CATALOGOS_TTL)
    cache.set("fallas_trabajadores", trabajadores, CATALOGOS_TTL)

    return severidades, tipos_falla, maquinas, estados, trabajadores, True


class ReporteFalla(generic.View):
    template_name = "fallas/reporte_falla.html"
    context = {}
    url_create = f"{API_URL}/v2/reportes/create/"
    response = None
    payload = {}

    def get(self, request):
        severidades, tipos_falla, maquinas, estados, trabajadores, ok = _cargar_catalogos()
        if not ok:
            messages.warning(request, "No se pudo conectar con la API para cargar los catálogos.")
        self.context = {
            "severidades": severidades,
            "tipos_falla": tipos_falla,
            "maquinas": maquinas,
            "estados": estados,
            "trabajadores": trabajadores,
            "seccion": "fallas",
            "subseccion": "reporte",
        }
        return render(request, self.template_name, self.context)

    def post(self, request):
        self.payload = {
            "asunto": request.POST.get("asunto"),
            "descripcion": request.POST.get("descripcion"),
            "causaRaiz": request.POST.get("causaRaiz"),
            "tiempoParo": request.POST.get("tiempoParo"),
            "fechaResolucion": request.POST.get("fechaSolucion") or None,
            "maquina": request.POST.get("maquina"),
            "trabajador": request.POST.get("trabajador"),
            "tipo_severidad": request.POST.get("tipo_severidad"),
            "estado_reporte": request.POST.get("estado_reporte"),
        }

        tipo_falla_ids = []
        valor_base = request.POST.get("tipo_falla")
        if valor_base:
            tipo_falla_ids.append(int(valor_base))

        idx = 1
        while True:
            val = request.POST.get(f"tipo_falla_{idx}")
            if val is None:
                break
            if val:
                tipo_falla_ids.append(int(val))
            idx += 1

        self.payload["tipo_falla_ids"] = tipo_falla_ids

        archivo = request.FILES.get("imagen")
        files = {"imagen": archivo} if archivo else None
        try:
            self.response = SESSION.post(url=self.url_create, data=self.payload, files=files, timeout=10)
        except requests.exceptions.RequestException:
            messages.warning(request, "No se pudo conectar con la API para registrar el reporte")
            return redirect("fallas:reporte")
        if self.response.status_code == 201:
            # invalidar el cache de la lista: el reporte recien creado debe
            # aparecer de inmediato en "Ver reportes" y en el dashboard.
            cache.delete("fallas_reportes_list")
            messages.success(request, "El reporte de falla ha sido registrado")
            return redirect("fallas:lista")
        else:
            messages.warning(request, "Error al registrar el reporte")
            return redirect("fallas:reporte")


class ListaReportes(generic.View):
    template_name = "fallas/lista_reportes.html"
    context = {}
    url_base = f"{API_URL}/v1/reportes/list/"
    response = None

    def get(self, request):
        # mismo cache key que usa el dashboard de usuarios: si alguien entro
        # a cualquiera de las dos pantallas hace menos de 15 seg, se reusa.
        reportes = cache.get("fallas_reportes_list")
        if reportes is None:
            try:
                reportes = SESSION.get(url=self.url_base, timeout=5).json()
                cache.set("fallas_reportes_list", reportes, REPORTES_TTL)
            except (requests.exceptions.RequestException, ValueError):
                reportes = []
                messages.warning(request, "No se pudo conectar con la API para cargar los reportes.")
        self.context = {
            "reportes": reportes,
            "seccion": "fallas",
            "subseccion": "lista",
        }
        return render(request, self.template_name, self.context)
    

class DetailReporte(generic.View):
    template_name = "fallas/fallas-modal/ver-detalle.html"
    context = {}

    def get(self, request, pk):
        cache_key = f"fallas_reporte_{pk}"
        reporte = cache.get(cache_key)

        if reporte is None:
            try:
                resp = SESSION.get(f"{API_URL}/v1/reportes/{pk}/", timeout=5)
                if resp.status_code != 200:
                    return render(request, self.template_name, {"reporte": None})
                reporte = resp.json()
                cache.set(cache_key, reporte, 30)
            except (requests.exceptions.RequestException, ValueError):
                return render(request, self.template_name, {"reporte": None})

        self.context = {"reporte": reporte}
        return render(request, self.template_name, self.context)


class ActualizarReporte(generic.View):
    template_name = "fallas/actualizar_reporte.html"

    def get(self, request, pk):
        cache_key = f"fallas_reporte_{pk}"
        reporte = cache.get(cache_key)

        if reporte is None:
            try:
                resp = SESSION.get(f"{API_URL}/v1/reportes/{pk}/", timeout=5)
                if resp.status_code != 200:
                    messages.warning(request, "No se pudo cargar el reporte.")
                    return redirect("fallas:lista")
                reporte = resp.json()
                cache.set(cache_key, reporte, 30)
            except (requests.exceptions.RequestException, ValueError):
                messages.warning(request, "No se pudo conectar con la API.")
                return redirect("fallas:lista")

        severidades, tipos_falla, maquinas, estados, trabajadores, _ = _cargar_catalogos()

        context = {
            "reporte": reporte,
            "severidades": severidades,
            "tipos_falla": tipos_falla,
            "maquinas": maquinas,
            "estados": estados,
            "trabajadores": trabajadores,
        }
        return render(request, self.template_name, context)

    def post(self, request, pk):
        payload = {
            "asunto": request.POST.get("asunto"),
            "descripcion": request.POST.get("descripcion"),
            "causaRaiz": request.POST.get("causaRaiz"),
            "tiempoParo": request.POST.get("tiempoParo"),
            "fechaResolucion": request.POST.get("fechaSolucion") or None,
            "maquina": request.POST.get("maquina"),
            "trabajador": request.POST.get("trabajador"),
            "tipo_severidad": request.POST.get("tipo_severidad"),
            "estado_reporte": request.POST.get("estado_reporte"),
        }

        tipo_falla_ids = []
        valor_base = request.POST.get("tipo_falla")
        if valor_base:
            tipo_falla_ids.append(int(valor_base))
        idx = 1
        while True:
            val = request.POST.get(f"tipo_falla_{idx}")
            if val is None:
                break
            if val:
                tipo_falla_ids.append(int(val))
            idx += 1
        payload["tipo_falla_ids"] = tipo_falla_ids

        archivo = request.FILES.get("imagen")
        files = {"imagen": archivo} if archivo else None

        try:
            api_url = f"{API_URL}/v2/reportes/update/{pk}/"
            response = SESSION.patch(url=api_url, data=payload, files=files, timeout=10)
        except requests.exceptions.RequestException:
            messages.warning(request, "No se pudo conectar con la API para actualizar el reporte.")
            return redirect("fallas:actualizar_reporte", pk=pk)

        if response.status_code == 200:
            cache.delete(f"fallas_reporte_{pk}")
            cache.delete("fallas_reportes_list")
            messages.success(request, "El reporte ha sido actualizado correctamente.")
            return redirect("fallas:lista")
        else:
            messages.warning(request, "Error al actualizar el reporte.")
            return redirect("fallas:actualizar_reporte", pk=pk)


class InvalidarCacheReportes(generic.View):

    def post(self, request):
        cache.delete("fallas_reportes_list")
        return JsonResponse({"ok": True})

    
