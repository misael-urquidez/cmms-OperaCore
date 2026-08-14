import json
import requests
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views import View

API_URL = f"{settings.API_BASE_URL}/mantenimiento"
SESSION = requests.Session()

def _obtener_orden(folio):
    """Trae el detalle completo de una orden desde el API de mantenimiento."""
    try:
        resp = SESSION.get(f"{API_URL}/v1/ordenes/{folio}/", timeout=5)
        if resp.status_code != 200:
            return None
        return resp.json()
    except (requests.exceptions.RequestException, ValueError):
        return None

def _obtener_lista(url):
    try:
        r = SESSION.get(url, timeout=5)
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return []

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
        return render(request, self.template_name, {"seccion":"mantenimiento", "base_template":"base_tecni.html" if usuario.get("rol") == "TECNI" else "base_admin.html", "es_tecnico":usuario.get("rol") == "TECNI", "es_admin":usuario.get("rol") == "ADMIN", "usuario":usuario, "trabajadores":obtener(f"{settings.API_BASE_URL}/fallas/v1/trabajadores/"), "maquinas":obtener(f"{settings.API_BASE_URL}/monitoreo/maquinas/"), "estados":obtener(f"{API_URL}/v1/estado-orden/list/"), "tipos_mantenimiento":obtener(f"{API_URL}/v1/tipo-mantenimiento/list/"), "piezas":obtener(f"{settings.API_BASE_URL}/inventario/v1/piezas/list/"), "refacciones":obtener(f"{settings.API_BASE_URL}/inventario/v1/refacciones/list/"), "herramientas":obtener(f"{settings.API_BASE_URL}/inventario/v1/herramientas/list/"), "tareas":obtener(f"{API_URL}/v1/tareas/list/")})


class DocumentoOrden(View):
    """Vista de solo lectura de una orden, con acceso a edición y exportación."""
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
        # Piezas SI se filtran por la maquina de la orden (igual que en el
        # drawer de "Mis ordenes"); las refacciones se dejan completas.
        todas_piezas = _obtener_lista(f"{settings.API_BASE_URL}/inventario/v1/piezas/list/")
        # Movimientos de inventario (refacciones/piezas) registrados para esta orden.
        movimientos = [
            m for m in _obtener_lista(f"{API_URL}/v1/movimientos/list/")
            if m.get("orden_mantenimiento") == folio
        ]
        context = {
            "orden": orden,
            "usuario": usuario,
            "es_tecnico": es_tecnico,
            "puede_modificar": (not es_tecnico) or (not orden_cerrada),
            # Estas dos controlan si se muestra el bloque "Completar orden"
            # (tecnico + orden abierta) y en que paso: iniciar o cerrar.
            "puede_iniciar": es_tecnico and orden.get("estado_orden") in ("PROGR", "SOLIC"),
            "puede_cerrar": es_tecnico and orden.get("estado_orden") == "ENPRO",
            "piezas": [p for p in todas_piezas if p.get("maquina") == orden.get("maquina")],
            "refacciones": _obtener_lista(f"{settings.API_BASE_URL}/inventario/v1/refacciones/list/"),
            "movimientos": movimientos,
            "base_template": "base_tecni.html" if es_tecnico else "base_admin.html",
        }
        return render(request, self.template_name, context)

class ProxyOrden(View):
    action = None
    def responder(self, request, folio=None):
        params = {k: request.GET[k] for k in ("trabajador", "estado", "tipo_mantenimiento") if request.GET.get(k)}
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


class OrdenUpdateAPIView(View):
    def patch(self, request, folio):
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except ValueError:
            return JsonResponse({"detail": "JSON inválido."}, status=400)
        try:
            r = SESSION.patch(
                f"{API_URL}/v2/ordenes/{folio}/update/",
                json=payload, timeout=5,
            )
            cuerpo = r.json()
        except (requests.RequestException, ValueError):
            return JsonResponse({"detail": "No fue posible conectar con el API."}, status=502)
        return JsonResponse(cuerpo, safe=False, status=r.status_code)


class OrdenDetalleAPIView(View):
    """Proxy GET del detalle de una orden (incluye tareas, herramientas y
    trabajadores asociados) para el drawer de edicion."""

    def get(self, request, folio):
        try:
            r = SESSION.get(f"{API_URL}/v1/ordenes/{folio}/", timeout=5)
            cuerpo = r.json()
        except (requests.RequestException, ValueError):
            return JsonResponse({"detail": "No fue posible conectar con el API."}, status=502)
        return JsonResponse(cuerpo, safe=False, status=r.status_code)


class OrdenCancelarAPIView(View):
    """Proxy PATCH hacia mantenimiento/v2/ordenes/<folio>/cancelar/ (marca
    la orden como CANCE)."""

    def patch(self, request, folio):
        try:
            r = SESSION.patch(f"{API_URL}/v2/ordenes/{folio}/cancelar/", timeout=5)
            cuerpo = r.json()
        except (requests.RequestException, ValueError):
            return JsonResponse({"detail": "No fue posible conectar con el API."}, status=502)
        return JsonResponse(cuerpo, safe=False, status=r.status_code)


class TareaCrearAPIView(View):
    """Proxy POST hacia mantenimiento/v2/tareas/create/ para que un admin
    pueda dar de alta una tarea nueva sobre la marcha en el modal de Nueva
    orden."""

    def post(self, request):
        try:
            r = SESSION.post(
                f"{API_URL}/v2/tareas/create/",
                json=json.loads(request.body.decode() or "{}"),
                timeout=10,
            )
            cuerpo = r.json()
        except (requests.RequestException, ValueError):
            return JsonResponse({"detail": "No fue posible conectar con el API."}, status=502)
        return JsonResponse(cuerpo, safe=False, status=r.status_code)


class TareaOrdenVerificarAPIView(View):
    """Proxy PATCH hacia mantenimiento/v1/tarea-orden/<tarea>/<folio>/ para
    marcar/desmarcar la verificacion (booleano) de una tarea del checklist
    del tecnico. El API recalcula el porcentaje de la orden."""

    def patch(self, request, folio, tarea):
        try:
            r = SESSION.patch(
                f"{API_URL}/v1/tarea-orden/{tarea}/{folio}/",
                json=json.loads(request.body.decode() or "{}"),
                timeout=5,
            )
            cuerpo = r.json()
        except (requests.RequestException, ValueError):
            return JsonResponse({"detail": "No fue posible conectar con el API."}, status=502)
        return JsonResponse(cuerpo, safe=False, status=r.status_code)


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


class _ExportarOrdenBase(View):
    formato = None

    def get(self, request, folio):
        url = f"{API_URL}/v1/ordenes/{folio}/export/{self.formato}/"
        qs = request.META.get("QUERY_STRING", "")
        if qs:
            url += f"?{qs}"
        try:
            resp = SESSION.get(url, timeout=15)
        except requests.RequestException:
            return HttpResponse("Error de conexion con la API", status=502)

        if resp.status_code != 200:
            return HttpResponse("Error al generar el archivo", status=resp.status_code)

        response = HttpResponse(resp.content, content_type=resp.headers.get("Content-Type", "application/octet-stream"))
        response["Content-Disposition"] = resp.headers.get("Content-Disposition", f'attachment; filename="orden_mantenimiento_{folio}.{self.formato}"')
        return response


class ExportarOrdenCSV(_ExportarOrdenBase):
    formato = "csv"


class ExportarOrdenXLSX(_ExportarOrdenBase):
    formato = "xlsx"


class ExportarOrdenPDF(_ExportarOrdenBase):
    formato = "pdf"


class CalendarioView(View):
    template_name = "mantenimiento/calendario.html"

    def get(self, request):
        usuario = request.session.get("usuario")
        if not usuario:
            messages.warning(request, "Inicia sesión para continuar.")
            return redirect("usuarios:index")

        def obtener(url):
            try:
                r = SESSION.get(url, timeout=5); r.raise_for_status(); return r.json()
            except requests.RequestException:
                return []

        context = {
            "seccion": "mantenimiento",
            "subseccion": "calendario",
            "base_template": "base_tecni.html" if usuario.get("rol") == "TECNI" else "base_admin.html",
            "es_tecnico": usuario.get("rol") == "TECNI",
            "usuario": usuario,
            "trabajadores": obtener(f"{settings.API_BASE_URL}/fallas/v1/trabajadores/"),
            "maquinas": obtener(f"{settings.API_BASE_URL}/monitoreo/maquinas/"),
            "tipos_mantenimiento": obtener(f"{API_URL}/v1/tipo-mantenimiento/list/"),
            "datos_url": f"{API_URL}/v1/ordenes/list/",
        }
        return render(request, self.template_name, context)


class TrabajadoresListView(View):
    template_name = "mantenimiento/trabajadores_lista.html"

    def get(self, request):
        usuario = request.session.get("usuario")
        if not usuario:
            messages.warning(request, "Inicia sesión para continuar.")
            return redirect("usuarios:index")

        trabajadores = _obtener_lista(f"{settings.API_BASE_URL}/usuarios/v1/trabajadores/list/")

        return render(request, self.template_name, {
            "seccion": "mantenimiento",
            "subseccion": "trabajadores",
            "base_template": "base_tecni.html" if usuario.get("rol") == "TECNI" else "base_admin.html",
            "es_tecnico": usuario.get("rol") == "TECNI",
            "usuario": usuario,
            "trabajadores": trabajadores,
        })


class TrabajadorDetalleView(View):
    """Perfil de un trabajador: datos, indicadores y actividad
    (ordenes de mantenimiento + reportes de falla que ha atendido)."""

    template_name = "mantenimiento/trabajador_detalle.html"

    def get(self, request, numeroNomina):
        usuario = request.session.get("usuario")
        if not usuario:
            messages.warning(request, "Inicia sesión para continuar.")
            return redirect("usuarios:index")

        trabajador = None
        try:
            resp = SESSION.get(f"{settings.API_BASE_URL}/usuarios/v1/trabajadores/{numeroNomina}/", timeout=5)
            if resp.status_code == 200:
                trabajador = resp.json()
        except requests.exceptions.RequestException:
            trabajador = None

        if trabajador is None:
            messages.warning(request, "No se pudo cargar ese trabajador.")
            return redirect("mantenimiento:trabajadores-lista")

        ordenes = _obtener_lista(
            f"{settings.API_BASE_URL}/mantenimiento/v1/ordenes/list/?trabajador={numeroNomina}"
        )
        reportes = _obtener_lista(
            f"{settings.API_BASE_URL}/fallas/v1/reportes/list/?trabajador={numeroNomina}"
        )

        # Contadores del encabezado via sp_perfil_trabajador (SP 8)
        contadores = _obtener_lista(
            f"{settings.API_BASE_URL}/usuarios/v1/trabajadores/{numeroNomina}/perfil/"
        ) or {}

        ESTADOS_CERRADOS = ("CERRA", "CANCE")
        ordenes_pendientes = [o for o in ordenes if o.get("estado_orden") not in ESTADOS_CERRADOS]
        ordenes_cerradas = [o for o in ordenes if o.get("estado_orden") == "CERRA"]

        # Maquinas distintas tocadas via ordenes o reportes (dict para deduplicar por codigo)
        maquinas_vistas = {}
        for o in ordenes:
            if o.get("maquina"):
                maquinas_vistas[o["maquina"]] = o.get("maquina_nombre")
        for r in reportes:
            if r.get("maquina"):
                maquinas_vistas[r["maquina"]] = r.get("maquina_nombre")
        maquinas_atendidas = [
            {"codigo": codigo, "nombre": nombre} for codigo, nombre in maquinas_vistas.items()
        ]

        # Linea de tiempo combinada, ordenada por fecha/hora descendente
        actividad = []
        for o in ordenes:
            actividad.append({
                "tipo": "orden",
                "fecha": o.get("fechacreacion"),
                "hora": o.get("horacreacion"),
                "titulo": f"Orden {o.get('folio')}",
                "detalle": o.get("descripcion"),
                "maquina_nombre": o.get("maquina_nombre"),
                "estado": o.get("estado_orden_nombre"),
                "folio": o.get("folio"),
            })
        for r in reportes:
            actividad.append({
                "tipo": "falla",
                "fecha": r.get("fechaCreacion"),
                "hora": r.get("horaCreacion"),
                "titulo": r.get("asunto"),
                "detalle": r.get("descripcion"),
                "maquina_nombre": r.get("maquina_nombre"),
                "estado": r.get("tipo_severidad_nombre"),
                "numeroRegistro": r.get("numeroRegistro"),
            })
        actividad.sort(key=lambda a: (a["fecha"] or "", a["hora"] or ""), reverse=True)

        return render(request, self.template_name, {
            "seccion": "mantenimiento",
            "subseccion": "trabajadores",
            "base_template": "base_tecni.html" if usuario.get("rol") == "TECNI" else "base_admin.html",
            "es_tecnico": usuario.get("rol") == "TECNI",
            "usuario": usuario,
            "trabajador": trabajador,
            "ordenes": ordenes,                     # NUEVO
            "ordenes_cerradas": ordenes_cerradas,    # NUEVO
            "ordenes_pendientes": ordenes_pendientes,
            "reportes": reportes,                    # NUEVO
            "total_ordenes": contadores.get("ordenes_asignadas") or 0,
            "total_cerradas": contadores.get("ordenes_cerradas") or 0,
            "total_pendientes": contadores.get("ordenes_pendientes") or 0,
            "total_reportes": contadores.get("fallas_reportadas") or 0,
            "total_maquinas": contadores.get("maquinas_atendidas") or 0,
            "maquinas_atendidas": maquinas_atendidas,
            "actividad": actividad,
        })