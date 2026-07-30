import io
import json
import requests
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.views import View
from xhtml2pdf import pisa

API_URL = f"{settings.API_BASE_URL}/mantenimiento"
SESSION = requests.Session()


def _obtener_orden(folio):
    """Trae el detalle completo de una orden (incluye diagnostico, notas,
    horasIntervenidas, etc. -- datos que /v1/ordenes/list/ NO manda) desde
    api/mantenimiento/v1/ordenes/<folio>/. Mismo patron que _obtener_reporte
    en fallas/views.py."""
    try:
        resp = SESSION.get(f"{API_URL}/v1/ordenes/{folio}/", timeout=5)
        if resp.status_code != 200:
            return None
        return resp.json()
    except (requests.exceptions.RequestException, ValueError):
        return None

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
        return render(request, self.template_name, {"seccion":"mantenimiento", "base_template":"base_tecni.html" if usuario.get("rol") == "TECNI" else "base_admin.html", "es_tecnico":usuario.get("rol") == "TECNI", "usuario":usuario, "trabajadores":obtener(f"{settings.API_BASE_URL}/fallas/v1/trabajadores/"), "maquinas":obtener(f"{settings.API_BASE_URL}/monitoreo/maquinas/"), "estados":obtener(f"{API_URL}/v1/estado-orden/list/"), "tipos_mantenimiento":obtener(f"{API_URL}/v1/tipo-mantenimiento/list/"), "piezas":obtener(f"{settings.API_BASE_URL}/inventario/v1/piezas/list/"), "refacciones":obtener(f"{settings.API_BASE_URL}/inventario/v1/refacciones/list/")})

class DocumentoOrden(View):
    """Vista de solo lectura de una orden (pensada para ordenes CERRADAS):
    muestra diagnostico/notas/horas ya capturados y da acceso a 'Descargar
    PDF'. Esta es la pantalla a la que debe mandar el click en una tarjeta
    de orden cerrada, en vez de abrir el drawer de edicion."""
    template_name = "mantenimiento/documento_orden.html"

    def get(self, request, folio):
        usuario = request.session.get("usuario")
        if not usuario:
            messages.warning(request, "Inicia sesión para continuar.")
            return redirect("usuarios:index")

        orden = _obtener_orden(folio)
        if orden is None:
            messages.warning(request, "No se pudo cargar la orden.")
            return redirect("mantenimiento:index")

        es_tecnico = usuario.get("rol") == "TECNI"
        orden_cerrada = orden.get("estado_orden") in ("CERRA", "CANCE")

        context = {
            "orden": orden,
            "usuario": usuario,
            "es_tecnico": es_tecnico,
            # El admin siempre puede modificar una orden; el tecnico solo
            # mientras siga abierta (no CERRAda ni CANCElada).
            "puede_modificar": (not es_tecnico) or (not orden_cerrada),
            "base_template": "base_tecni.html" if es_tecnico else "base_admin.html",
        }
        return render(request, self.template_name, context)


class DocumentoOrdenPDF(View):
    """Genera el documento de la orden en PDF (xhtml2pdf) y lo manda como
    descarga. Mismo patron que DocumentoReportePDF en fallas/views.py."""

    def get(self, request, folio):
        usuario = request.session.get("usuario")
        if not usuario:
            messages.warning(request, "Inicia sesión para continuar.")
            return redirect("usuarios:index")

        orden = _obtener_orden(folio)
        if orden is None:
            messages.warning(request, "No se pudo cargar la orden.")
            return redirect("mantenimiento:index")

        html = render_to_string("mantenimiento/documento_orden_pdf.html", {"orden": orden})
        buffer = io.BytesIO()
        resultado = pisa.CreatePDF(html, dest=buffer)
        if resultado.err:
            buffer.close()
            messages.warning(request, "No se pudo generar el PDF de la orden.")
            return redirect("mantenimiento:documento_orden", folio=folio)

        pdf = buffer.getvalue()
        buffer.close()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="orden_{folio}.pdf"'
        return response


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


class MovimientoCrearAPIView(View):
    """Proxy JSON hacia mantenimiento/v2/movimientos/create/, reusando el
    modulo de inventario que ya construyo fix-sql. Se llama una vez por
    cada pieza/refaccion agregada al cerrar una orden."""
    def post(self, request):
        try:
            r = SESSION.post(
                f"{API_URL}/v2/movimientos/create/",
                json=json.loads(request.body.decode() or "{}"),
                timeout=10,
            )
            cuerpo = r.json()
        except (requests.RequestException, ValueError):
            return JsonResponse({"detail": "No fue posible conectar con el API."}, status=502)
        return JsonResponse(cuerpo, safe=False, status=r.status_code)