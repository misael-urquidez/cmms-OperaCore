import json
import requests
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import View

API_URL = f"{settings.API_BASE_URL}/mantenimiento"
SESSION = requests.Session()

class Index(View):
    template_name = "mantenimiento/index.html"
    def get(self, request):
        usuario = request.session.get("usuario")
        if not usuario:
            messages.warning(request, "Inicia sesión para continuar.")
            return redirect("usuarios:index")
        def obtener(url):
            try:
                r = SESSION.get(url, timeout=5); r.raise_for_status(); return r.json()
            except requests.RequestException: return []
        return render(request, self.template_name, {"seccion":"mantenimiento", "base_template":"base_tecni.html" if usuario.get("rol") == "TECNI" else "base_admin.html", "es_tecnico":usuario.get("rol") == "TECNI", "usuario":usuario, "trabajadores":obtener(f"{settings.API_BASE_URL}/fallas/v1/trabajadores/"), "maquinas":obtener(f"{settings.API_BASE_URL}/monitoreo/maquinas/"), "estados":obtener(f"{API_URL}/v1/estado-orden/list/")})

class ProxyOrden(View):
    action = None
    def responder(self, request, folio=None):
        params = {k: request.GET[k] for k in ("trabajador", "estado") if request.GET.get(k)}
        endpoint = "v1/ordenes/list/" if self.action == "list" else f"v2/ordenes/{folio}/{self.action}/"
        if self.action == "create": endpoint = "v2/ordenes/create/"
        try:
            if self.action == "list": r = SESSION.get(f"{API_URL}/{endpoint}", params=params, timeout=5)
            else: r = SESSION.request("POST" if self.action == "create" else "PATCH", f"{API_URL}/{endpoint}", json=json.loads(request.body.decode() or "{}"), timeout=5)
            cuerpo = r.json()
        except (requests.RequestException, ValueError): return JsonResponse({"detail":"No fue posible conectar con el API."}, status=502)
        return JsonResponse(cuerpo, safe=False, status=r.status_code)
    def get(self, request, folio=None): return self.responder(request, folio)
    def post(self, request, folio=None): return self.responder(request, folio)
    def patch(self, request, folio=None): return self.responder(request, folio)

class ReportesDisponiblesAPIView(View):
    def get(self, request):
        params = {}
        if request.GET.get("maquina"):
            params["maquina"] = request.GET["maquina"]
        try:
            r = SESSION.get(f"{API_URL}/v1/reportes-disponibles/list/", params=params, timeout=5)
            cuerpo = r.json()
        except (requests.RequestException, ValueError):
            return JsonResponse({"detail": "No fue posible conectar con el API."}, status=502)
        return JsonResponse(cuerpo, safe=False, status=r.status_code)


class OrdenesListAPIView(ProxyOrden): action = "list"
class OrdenCrearAPIView(ProxyOrden): action = "create"
class OrdenAsignarAPIView(ProxyOrden): action = "asignar"
class OrdenIniciarAPIView(ProxyOrden): action = "iniciar"
class OrdenCerrarAPIView(ProxyOrden): action = "cerrar"
