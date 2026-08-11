import json
import requests
from collections import defaultdict
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import generic

from apps.gestion.registry import get_tabla

API_URL = f"{settings.API_BASE_URL}/inventario"
MANTENIMIENTO_API_URL = f"{settings.API_BASE_URL}/mantenimiento"

# Sesion HTTP a nivel de modulo: reusa la conexion TCP con el api/.
SESSION = requests.Session()

# Cache de 30 segundos para el ping del modulo.
PING_TTL = 30

def _cargar_catalogos():
    """Carga los catalogos del API y los devuelve como un diccionario.
    Usa cache para no pegarle al API en cada request."""
    cache_key = "inventario_catalogos"
    catalogos = cache.get(cache_key)
    if catalogos is not None:
        return catalogos, True

    try:
        res = SESSION.get(f"{API_URL}/v1/catalogos/", timeout=5)
        if res.status_code == 200:
            catalogos = res.json()
            cache.set(cache_key, catalogos, 300)  # 5 minutos
            return catalogos, True
    except requests.exceptions.RequestException:
        pass
    return {}, False

def _columnas_config(nombres):
    """Convierte nombres de columna (strings) en dicts {name, label},
    que es lo que esperan los templates de lista (patrón de gestion)."""
    etiquetas = {
        "numeroregistro": "Registro",
        "numeroserie": "No. serie",
        "codigosku": "Código SKU",
        "codigoinventario": "Código inventario",
        "stockminimo": "Stock mínimo",
        "puntoreorden": "Punto de reorden",
        "tiempoentregaapr": "Tiempo entrega",
        "porcentaje_desgaste": "% Desgaste",
        "depresacionanual": "Dep. anual",
        "costoinicial": "Costo inicial",
        "valorresidual": "Valor residual",
        "horasoperacion": "Horas operación",
        "tiempovidautil": "Vida útil",
        "fechainstalacion": "Fecha instalación",
        "fechagarantia": "Fecha garantía",
        "edo_pieza": "Estado",
        "tipo_pieza": "Tipo",
        "tipo_refaccion": "Tipo",
    }
    def etiqueta(nombre):
        if nombre in etiquetas:
            return etiquetas[nombre]
        return nombre.replace("_", " ").capitalize()
    return [{"name": n, "label": etiqueta(n)} for n in nombres]


def _base_template(request):
    """Devuelve el template base a usar (admin o tecnico)."""
    usuario = request.session.get("usuario")
    return "base_tecni.html" if usuario and usuario.get("rol") == "TECNI" else "base_admin.html"


class Index(generic.View):
    """Pantalla principal del modulo Inventario. Consume el api/ por HTTP."""

    template_name = "inventario/index.html"

    def get(self, request):
        usuario = request.session.get("usuario")
        if not usuario:
            messages.warning(request, "Inicia sesión para continuar.")
            return redirect("usuarios:index")
        response = cache.get("inventario_ping")
        if response is None:
            try:
                response = SESSION.get(f"{API_URL}/ping/", timeout=5).json()
            except requests.exceptions.RequestException:
                response = {"status": "sin conexion con el api"}
            cache.set("inventario_ping", response, PING_TTL)
        return render(request, self.template_name, {
            "modulo": "Inventario", "api_status": response,
            "seccion": "inventario", "subseccion": "panel",
            "base_template": _base_template(request),
        })


class ListaRefacciones(generic.View):
    """Lista de refacciones con buscador, filtros y exportación."""

    template_name = "inventario/lista_refacciones.html"

    def get(self, request):
        config = request.session.get("config_inventario", {})
        config.setdefault("pk_field", "numeroregistro")
        config.setdefault("pk_label", "ID")
        visibles = config.get("columnas", ["nombre", "codigosku", "stock", "stockminimo"])
        todas_las = ["nombre", "codigosku", "stock", "stockminimo", "descripcion", "costo", "proveedor", "clasificacion", "tipo", "ubicacion"]
        necesita_modal = any(c not in visibles for c in ["proveedor", "clasificacion", "tipo"])
        try:
            res = SESSION.get(f"{API_URL}/v1/refacciones/list/", timeout=8)
            if res.status_code != 200:
                raise requests.exceptions.RequestException
            registros = res.json()
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el API.")
            registros = []

        # KPI's para el dashboard
        reorden = sum(1 for r in registros if (r.get("stock") or 0) <= (r.get("stockminimo") or 0))
        stock_bajo = sum(1 for r in registros if (r.get("stock") or 0) < (r.get("stockminimo") or 0))
        buen_stock = sum(
            1 for r in registros
            if (r.get("stock") or 0) >= (r.get("stockminimo") or 0)
        )
        total_unidades = sum(r.get("stock") or 0 for r in registros)

        catalogos, _ = _cargar_catalogos()
        tipos_refaccion = catalogos.get("tipos_refaccion", [])
        clasificaciones = catalogos.get("clasificaciones", [])

        context = {
            "config": config,
            "registros": registros,
            "columnas": _columnas_config(visibles),
            "todas_las_columnas": _columnas_config(todas_las),
            "necesita_modal": necesita_modal,
            "seccion": "inventario",
            "subseccion": "refacciones",
            "base_template": _base_template(request),
            "kpi_reorden": reorden,
            "kpi_stock_bajo": stock_bajo,
            "kpi_buen_stock": buen_stock,
            "kpi_total_unidades": total_unidades,
            "tipos_refaccion": tipos_refaccion,
            "clasificaciones": clasificaciones,
        }
        return render(request, self.template_name, context)


class CrearRefaccion(generic.View):
    template_name = "inventario/crear_refaccion.html"

    def get(self, request):
        catalogos, ok = _cargar_catalogos()
        if not ok:
            messages.warning(request, "No se pudo conectar con la API para cargar catálogos.")

        context = {
            "catalogos": catalogos,
            "seccion": "inventario",
            "subseccion": "crear_refaccion",
            "base_template": _base_template(request),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        payload = {
            "nombre": request.POST.get("nombre"),
            "codigosku": request.POST.get("codigosku"),
            "puntoreorden": request.POST.get("puntoreorden"),
            "stockminimo": request.POST.get("stockminimo"),
            "stock": request.POST.get("stock"),
            "costo": request.POST.get("costo"),
            "proveedor": request.POST.get("proveedor"),
            "clasificacion": request.POST.get("clasificacion"),
            "tipo": request.POST.get("tipo"),
            "descripcion": request.POST.get("descripcion"),
            "ubicacion": request.POST.get("ubicacion"),
        }
        try:
            res = SESSION.post(f"{API_URL}/v2/refacciones/create/", json=payload, timeout=10)
            if res.status_code == 201:
                messages.success(request, "Refacción creada correctamente.")
                return redirect("inventario:lista_refacciones")
            else:
                messages.error(request, f"Error: {res.json().get('detail', 'No se pudo crear la refacción.')}")
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el API.")
        return redirect("inventario:crear_refaccion")


class ListaPiezas(generic.View):
    """Lista de piezas con buscador y filtros."""

    template_name = "inventario/lista_pieza.html"

    def get(self, request):
        config = request.session.get("config_inventario_piezas", {})
        config.setdefault("pk_field", "numeroserie")
        config.setdefault("pk_label", "Serie")
        visibles = config.get("columnas", ["nombre", "numeroserie", "maquina", "edo_pieza", "tipo_pieza", "porcentaje_desgaste"])
        todas_las = ["nombre", "numeroserie", "maquina", "edo_pieza", "tipo_pieza", "porcentaje_desgaste", "costoinicial", "fecha_instalacion", "descripcion"]

        try:
            res = SESSION.get(f"{API_URL}/v1/piezas/list/", timeout=8)
            if res.status_code != 200:
                raise requests.exceptions.RequestException
            piezas = res.json()
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el API.")
            piezas = []

        # Agrupar piezas por maquina
        maquinas_con_piezas = defaultdict(list)
        for pieza in piezas:
            maquinas_con_piezas[pieza["maquina"]].append(pieza)

        try:
            res = SESSION.get(f"{settings.API_BASE_URL}/fallas/v1/maquinas/", timeout=5)
            maquinas = res.json() if res.status_code == 200 else []
        except requests.exceptions.RequestException:
            maquinas = []

        catalogos, _ = _cargar_catalogos()
        estados_pieza = catalogos.get("estados_pieza", [])
        tipos_pieza = catalogos.get("tipos_pieza", [])

        context = {
            "config": config,
            "registros": piezas,
            "piezas": piezas,
            "maquinas": maquinas,
            "maquinas_con_piezas": dict(maquinas_con_piezas),
            "columnas": _columnas_config(visibles),
            "todas_las_columnas": _columnas_config(todas_las),
            "seccion": "inventario",
            "subseccion": "piezas",
            "base_template": _base_template(request),
            "estados_pieza": estados_pieza,
            "tipos_pieza": tipos_pieza,
        }
        return render(request, self.template_name, context)


class CrearPieza(generic.View):
    template_name = "inventario/crear_pieza.html"

    def get(self, request):
        catalogos, ok = _cargar_catalogos()
        if not ok:
            messages.warning(request, "No se pudo conectar con la API para cargar catálogos.")

        try:
            res = SESSION.get(f"{API_URL}/v1/maquinas/list/", timeout=5)
            maquinas = res.json() if res.status_code == 200 else []
        except requests.exceptions.RequestException:
            maquinas = []

        context = {
            "catalogos": catalogos,
            "maquinas": maquinas,
            "seccion": "inventario",
            "subseccion": "crear_pieza",
            "base_template": _base_template(request),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        payload = {
            "nombre": request.POST.get("nombre"),
            "numeroserie": request.POST.get("numeroserie"),
            "maquina": request.POST.get("maquina"),
            "estado": request.POST.get("estado"),
            "tipo": request.POST.get("tipo"),
            "costoinicial": request.POST.get("costoinicial"),
            "fecha_instalacion": request.POST.get("fecha_instalacion"),
            "descripcion": request.POST.get("descripcion"),
        }
        try:
            res = SESSION.post(f"{API_URL}/v2/piezas/create/", json=payload, timeout=10)
            if res.status_code == 201:
                messages.success(request, "Pieza creada correctamente.")
                return redirect("inventario:lista_piezas")
            else:
                messages.error(request, f"Error: {res.json().get('detail', 'No se pudo crear la pieza.')}")
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el API.")
        return redirect("inventario:crear_pieza")


class ListaHerramientas(generic.View):
    """Lista de herramientas con buscador y filtros."""

    template_name = "inventario/lista_herramientas.html"

    def get(self, request):
        config = request.session.get("config_inventario_herramientas", {})
        visibles = config.get("columnas", ["nombre", "codigo", "estado", "tipo", "ubicacion"])
        todas_las = ["nombre", "codigo", "estado", "tipo", "ubicacion", "descripcion"]

        try:
            res = SESSION.get(f"{API_URL}/v1/herramientas/list/", timeout=8)
            if res.status_code != 200:
                raise requests.exceptions.RequestException
            herramientas = res.json()
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el API.")
            herramientas = []

        catalogos, _ = _cargar_catalogos()
        estados_herramienta = catalogos.get("estados_herramienta", [])
        tipos_herramienta = catalogos.get("tipos_herramienta", [])

        context = {
            "config": config,
            "herramientas": herramientas,
            "columnas": visibles,
            "todas_las_columnas": todas_las,
            "seccion": "inventario",
            "subseccion": "herramientas",
            "base_template": _base_template(request),
            "estados_herramienta": estados_herramienta,
            "tipos_herramienta": tipos_herramienta,
        }
        return render(request, self.template_name, context)


class CrearHerramienta(generic.View):
    template_name = "inventario/crear_herramienta.html"

    def get(self, request):
        catalogos, ok = _cargar_catalogos()
        if not ok:
            messages.warning(request, "No se pudo conectar con la API para cargar catálogos.")

        context = {
            "catalogos": catalogos,
            "seccion": "inventario",
            "subseccion": "crear_herramienta",
            "base_template": _base_template(request),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        payload = {
            "nombre": request.POST.get("nombre"),
            "codigo": request.POST.get("codigo"),
            "estado": request.POST.get("estado"),
            "tipo": request.POST.get("tipo"),
            "ubicacion": request.POST.get("ubicacion"),
            "descripcion": request.POST.get("descripcion"),
        }
        try:
            res = SESSION.post(f"{API_URL}/v2/herramientas/create/", json=payload, timeout=10)
            if res.status_code == 201:
                messages.success(request, "Herramienta creada correctamente.")
                return redirect("inventario:lista_herramientas")
            else:
                messages.error(request, f"Error: {res.json().get('detail', 'No se pudo crear la herramienta.')}")
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el API.")
        return redirect("inventario:crear_herramienta")


class ListaMovimientos(generic.View):
    """Lista de movimientos de inventario con buscador y filtros."""

    template_name = "inventario/lista_movimientos.html"

    def get(self, request):
        config = request.session.get("config_inventario_movimientos", {})
        visibles = config.get("columnas", ["fecha", "tipo", "refaccion", "cantidad", "usuario"])
        todas_las = ["fecha", "tipo", "refaccion", "cantidad", "usuario", "notas"]

        try:
            res = SESSION.get(f"{API_URL}/v1/movimientos/list/", timeout=8)
            if res.status_code != 200:
                raise requests.exceptions.RequestException
            movimientos = res.json()
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el API.")
            movimientos = []

        context = {
            "config": config,
            "registros": movimientos,
            "movimientos": movimientos,
            "columnas": visibles,
            "todas_las_columnas": todas_las,
            "tipos_movimiento": [
                {"codigo": "INSTA", "descripcion": "Instalación"},
                {"codigo": "DESMO", "descripcion": "Desmontaje"},
                {"codigo": "REHA", "descripcion": "Rehabilitación"},
            ],
            "seccion": "inventario",
            "subseccion": "movimientos",
            "base_template": _base_template(request),
        }
        return render(request, self.template_name, context)


class CrearMovimiento(generic.View):
    template_name = "inventario/crear_movimiento.html"

    def get(self, request):
        datos = {}
        orden_pre = request.GET.get("orden")
        if orden_pre:
            datos["orden_mantenimiento"] = orden_pre
        return render(request, self.template_name, _contexto_movimiento(request, datos))

    def post(self, request):
        payload = {
            "tipoMovimiento": request.POST.get("tipoMovimiento"),
            "fecha": request.POST.get("fecha"),
            "hora": request.POST.get("hora"),
            "orden_mantenimiento": request.POST.get("orden_mantenimiento") or None,
            "refaccion": request.POST.get("refaccion") or None,
            "pieza": request.POST.get("pieza") or None,
            "descripcion": request.POST.get("descripcion") or None,
        }
        pieza_data = {
            k[len("pieza_"):]: v
            for k, v in request.POST.items()
            if k.startswith("pieza_") and v
        }
        if pieza_data:
            payload["pieza_data"] = pieza_data

        try:
            res = SESSION.post(
                f"{MANTENIMIENTO_API_URL}/v2/movimientos/create/",
                json=payload,
                timeout=10,
            )
            if res.status_code == 201:
                messages.success(request, "Movimiento registrado correctamente.")
                return redirect("inventario:lista_movimientos")
            else:
                try:
                    body = res.json()
                except ValueError:
                    body = {}
                detail = body.get("detail", "No se pudo registrar el movimiento.") if isinstance(body, dict) else (body or "No se pudo registrar el movimiento.")
                if isinstance(detail, list):
                    detail = "; ".join(str(d) for d in detail)
                elif not isinstance(detail, str):
                    detail = str(detail)
                messages.error(request, f"Error: {detail}")
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el API.")

        # Error: re-render con los datos del formulario para no perder lo escrito.
        datos = {
            "tipoMovimiento": request.POST.get("tipoMovimiento") or "",
            "fecha": request.POST.get("fecha") or "",
            "hora": request.POST.get("hora") or "",
            "orden_mantenimiento": request.POST.get("orden_mantenimiento") or "",
            "refaccion": request.POST.get("refaccion") or "",
            "descripcion": request.POST.get("descripcion") or "",
        }
        pieza_value = request.POST.get("pieza")
        if pieza_value:
            datos["pieza"] = [pieza_value]
        for k, v in pieza_data.items():
            datos[f"pieza_{k}"] = [v]
        return render(request, self.template_name, _contexto_movimiento(request, datos))


def _contexto_movimiento(request, datos):
    """Contexto compartido del alta de movimiento: catalogos y listas que el
    template y movimiento.js esperan (refacciones, piezas, ordenes, maquinas)."""
    catalogos, ok = _cargar_catalogos()
    if not ok:
        messages.warning(request, "No se pudo conectar con la API para cargar catálogos.")

    def _get(url):
        try:
            res = SESSION.get(url, timeout=5)
            return res.json() if res.status_code == 200 else []
        except requests.exceptions.RequestException:
            return []

    return {
        "datos": datos,
        "catalogos": catalogos,
        "refacciones": _get(f"{API_URL}/v1/refacciones/list/"),
        "piezas": _get(f"{API_URL}/v1/piezas/list/"),
        "ordenes": _get(f"{MANTENIMIENTO_API_URL}/v1/ordenes/list/"),
        "maquinas": _get(f"{settings.API_BASE_URL}/fallas/v1/maquinas/"),
        "tipos_pieza": catalogos.get("tipos_pieza", []),
        "estados_pieza": catalogos.get("estados_pieza", []),
        "seccion": "inventario",
        "subseccion": "crear_movimiento",
        "base_template": _base_template(request),
    }


class ListaProveedores(generic.View):
    """Lista de proveedores con buscador."""

    template_name = "inventario/lista_proveedores.html"

    def get(self, request):
        config = request.session.get("config_inventario_proveedores", {})
        visibles = config.get("columnas", ["nombre", "contacto", "telefono", "correo"])
        todas_las = ["nombre", "contacto", "telefono", "correo", "direccion", "notas"]

        try:
            res = SESSION.get(f"{API_URL}/v1/proveedores/list/", timeout=8)
            if res.status_code != 200:
                raise requests.exceptions.RequestException
            proveedores = res.json()
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el API.")
            proveedores = []

        context = {
            "config": config,
            "proveedores": proveedores,
            "columnas": visibles,
            "todas_las_columnas": todas_las,
            "seccion": "inventario",
            "subseccion": "proveedores",
            "base_template": _base_template(request),
        }
        return render(request, self.template_name, context)


class CrearProveedor(generic.View):
    template_name = "inventario/crear_proveedor.html"

    def get(self, request):
        context = {
            "seccion": "inventario",
            "subseccion": "crear_proveedor",
            "base_template": _base_template(request),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        payload = {
            "nombre": request.POST.get("nombre"),
            "contacto": request.POST.get("contacto"),
            "telefono": request.POST.get("telefono"),
            "correo": request.POST.get("correo"),
            "direccion": request.POST.get("direccion"),
            "notas": request.POST.get("notas"),
        }
        try:
            res = SESSION.post(f"{API_URL}/v2/proveedores/create/", json=payload, timeout=10)
            if res.status_code == 201:
                messages.success(request, "Proveedor creado correctamente.")
                return redirect("inventario:lista_proveedores")
            else:
                messages.error(request, f"Error: {res.json().get('detail', 'No se pudo crear el proveedor.')}")
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el API.")
        return redirect("inventario:crear_proveedor")


class ListaClasificaciones(generic.View):
    """Lista de clasificaciones con buscador."""

    template_name = "inventario/lista_clasificaciones.html"

    def get(self, request):
        config = request.session.get("config_inventario_clasificaciones", {})
        visibles = config.get("columnas", ["nombre", "descripcion"])
        todas_las = ["nombre", "descripcion"]

        try:
            res = SESSION.get(f"{API_URL}/v1/clasificaciones/list/", timeout=8)
            if res.status_code != 200:
                raise requests.exceptions.RequestException
            clasificaciones = res.json()
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el API.")
            clasificaciones = []

        context = {
            "config": config,
            "clasificaciones": clasificaciones,
            "columnas": visibles,
            "todas_las_columnas": todas_las,
            "seccion": "inventario",
            "subseccion": "clasificaciones",
            "base_template": _base_template(request),
        }
        return render(request, self.template_name, context)


class CrearClasificacion(generic.View):
    template_name = "inventario/crear_clasificacion.html"

    def get(self, request):
        context = {
            "seccion": "inventario",
            "subseccion": "crear_clasificacion",
            "base_template": _base_template(request),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        payload = {
            "nombre": request.POST.get("nombre"),
            "descripcion": request.POST.get("descripcion"),
        }
        try:
            res = SESSION.post(f"{API_URL}/v2/clasificaciones/create/", json=payload, timeout=10)
            if res.status_code == 201:
                messages.success(request, "Clasificación creada correctamente.")
                return redirect("inventario:lista_clasificaciones")
            else:
                messages.error(request, f"Error: {res.json().get('detail', 'No se pudo crear la clasificación.')}")
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el API.")
        return redirect("inventario:crear_clasificacion")


class ListaEstadosHerramienta(generic.View):
    """Lista de estados de herramienta con buscador."""

    template_name = "inventario/lista_estados_herramienta.html"

    def get(self, request):
        config = request.session.get("config_inventario_estados_herramienta", {})
        visibles = config.get("columnas", ["nombre", "descripcion"])
        todas_las = ["nombre", "descripcion"]

        try:
            res = SESSION.get(f"{API_URL}/v1/estados-herramienta/list/", timeout=8)
            if res.status_code != 200:
                raise requests.exceptions.RequestException
            estados = res.json()
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el API.")
            estados = []

        context = {
            "config": config,
            "estados": estados,
            "columnas": visibles,
            "todas_las_columnas": todas_las,
            "seccion": "inventario",
            "subseccion": "estados_herramienta",
            "base_template": _base_template(request),
        }
        return render(request, self.template_name, context)


class CrearEstadoHerramienta(generic.View):
    template_name = "inventario/crear_estado_herramienta.html"

    def get(self, request):
        context = {
            "seccion": "inventario",
            "subseccion": "crear_estado_herramienta",
            "base_template": _base_template(request),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        payload = {
            "nombre": request.POST.get("nombre"),
            "descripcion": request.POST.get("descripcion"),
        }
        try:
            res = SESSION.post(f"{API_URL}/v2/estados-herramienta/create/", json=payload, timeout=10)
            if res.status_code == 201:
                messages.success(request, "Estado de herramienta creado correctamente.")
                return redirect("inventario:lista_estados_herramienta")
            else:
                messages.error(request, f"Error: {res.json().get('detail', 'No se pudo crear el estado.')}")
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el API.")
        return redirect("inventario:crear_estado_herramienta")


class ListaEstadosPieza(generic.View):
    """Lista de estados de pieza con buscador."""

    template_name = "inventario/lista_estados_pieza.html"

    def get(self, request):
        config = request.session.get("config_inventario_estados_pieza", {})
        visibles = config.get("columnas", ["nombre", "descripcion"])
        todas_las = ["nombre", "descripcion"]

        try:
            res = SESSION.get(f"{API_URL}/v1/estados-pieza/list/", timeout=8)
            if res.status_code != 200:
                raise requests.exceptions.RequestException
            estados = res.json()
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el API.")
            estados = []

        context = {
            "config": config,
            "estados": estados,
            "columnas": visibles,
            "todas_las_columnas": todas_las,
            "seccion": "inventario",
            "subseccion": "estados_pieza",
            "base_template": _base_template(request),
        }
        return render(request, self.template_name, context)


class CrearEstadoPieza(generic.View):
    template_name = "inventario/crear_estado_pieza.html"

    def get(self, request):
        context = {
            "seccion": "inventario",
            "subseccion": "crear_estado_pieza",
            "base_template": _base_template(request),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        payload = {
            "nombre": request.POST.get("nombre"),
            "descripcion": request.POST.get("descripcion"),
        }
        try:
            res = SESSION.post(f"{API_URL}/v2/estados-pieza/create/", json=payload, timeout=10)
            if res.status_code == 201:
                messages.success(request, "Estado de pieza creado correctamente.")
                return redirect("inventario:lista_estados_pieza")
            else:
                messages.error(request, f"Error: {res.json().get('detail', 'No se pudo crear el estado.')}")
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el API.")
        return redirect("inventario:crear_estado_pieza")


class ListaEstadosRefaccion(generic.View):
    """Lista de estados de refacción con buscador."""

    template_name = "inventario/lista_estados_refaccion.html"

    def get(self, request):
        config = request.session.get("config_inventario_estados_refaccion", {})
        visibles = config.get("columnas", ["nombre", "descripcion"])
        todas_las = ["nombre", "descripcion"]

        try:
            res = SESSION.get(f"{API_URL}/v1/estados-refaccion/list/", timeout=8)
            if res.status_code != 200:
                raise requests.exceptions.RequestException
            estados = res.json()
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el API.")
            estados = []

        context = {
            "config": config,
            "estados": estados,
            "columnas": visibles,
            "todas_las_columnas": todas_las,
            "seccion": "inventario",
            "subseccion": "estados_refaccion",
            "base_template": _base_template(request),
        }
        return render(request, self.template_name, context)


class CrearEstadoRefaccion(generic.View):
    template_name = "inventario/crear_estado_refaccion.html"

    def get(self, request):
        context = {
            "seccion": "inventario",
            "subseccion": "crear_estado_refaccion",
            "base_template": _base_template(request),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        payload = {
            "nombre": request.POST.get("nombre"),
            "descripcion": request.POST.get("descripcion"),
        }
        try:
            res = SESSION.post(f"{API_URL}/v2/estados-refaccion/create/", json=payload, timeout=10)
            if res.status_code == 201:
                messages.success(request, "Estado de refacción creado correctamente.")
                return redirect("inventario:lista_estados_refaccion")
            else:
                messages.error(request, f"Error: {res.json().get('detail', 'No se pudo crear el estado.')}")
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el API.")
        return redirect("inventario:crear_estado_refaccion")


class ListaTiposHerramienta(generic.View):
    """Lista de tipos de herramienta con buscador."""

    template_name = "inventario/lista_tipos_herramienta.html"

    def get(self, request):
        config = request.session.get("config_inventario_tipos_herramienta", {})
        visibles = config.get("columnas", ["nombre", "descripcion"])
        todas_las = ["nombre", "descripcion"]

        try:
            res = SESSION.get(f"{API_URL}/v1/tipos-herramienta/list/", timeout=8)
            if res.status_code != 200:
                raise requests.exceptions.RequestException
            tipos = res.json()
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el API.")
            tipos = []

        context = {
            "config": config,
            "tipos": tipos,
            "columnas": visibles,
            "todas_las_columnas": todas_las,
            "seccion": "inventario",
            "subseccion": "tipos_herramienta",
            "base_template": _base_template(request),
        }
        return render(request, self.template_name, context)


class CrearTipoHerramienta(generic.View):
    template_name = "inventario/crear_tipo_herramienta.html"

    def get(self, request):
        context = {
            "seccion": "inventario",
            "subseccion": "crear_tipo_herramienta",
            "base_template": _base_template(request),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        payload = {
            "nombre": request.POST.get("nombre"),
            "descripcion": request.POST.get("descripcion"),
        }
        try:
            res = SESSION.post(f"{API_URL}/v2/tipos-herramienta/create/", json=payload, timeout=10)
            if res.status_code == 201:
                messages.success(request, "Tipo de herramienta creado correctamente.")
                return redirect("inventario:lista_tipos_herramienta")
            else:
                messages.error(request, f"Error: {res.json().get('detail', 'No se pudo crear el tipo.')}")
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el API.")
        return redirect("inventario:crear_tipo_herramienta")


class ListaTiposPieza(generic.View):
    """Lista de tipos de pieza con buscador."""

    template_name = "inventario/lista_tipos_pieza.html"

    def get(self, request):
        config = request.session.get("config_inventario_tipos_pieza", {})
        visibles = config.get("columnas", ["nombre", "descripcion"])
        todas_las = ["nombre", "descripcion"]

        try:
            res = SESSION.get(f"{API_URL}/v1/tipos-pieza/list/", timeout=8)
            if res.status_code != 200:
                raise requests.exceptions.RequestException
            tipos = res.json()
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el API.")
            tipos = []

        context = {
            "config": config,
            "tipos": tipos,
            "columnas": visibles,
            "todas_las_columnas": todas_las,
            "seccion": "inventario",
            "subseccion": "tipos_pieza",
            "base_template": _base_template(request),
        }
        return render(request, self.template_name, context)


class CrearTipoPieza(generic.View):
    template_name = "inventario/crear_tipo_pieza.html"

    def get(self, request):
        context = {
            "seccion": "inventario",
            "subseccion": "crear_tipo_pieza",
            "base_template": _base_template(request),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        payload = {
            "nombre": request.POST.get("nombre"),
            "descripcion": request.POST.get("descripcion"),
        }
        try:
            res = SESSION.post(f"{API_URL}/v2/tipos-pieza/create/", json=payload, timeout=10)
            if res.status_code == 201:
                messages.success(request, "Tipo de pieza creado correctamente.")
                return redirect("inventario:lista_tipos_pieza")
            else:
                messages.error(request, f"Error: {res.json().get('detail', 'No se pudo crear el tipo.')}")
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el API.")
        return redirect("inventario:crear_tipo_pieza")


class ListaTiposRefaccion(generic.View):
    """Lista de tipos de refacción con buscador."""

    template_name = "inventario/lista_tipos_refaccion.html"

    def get(self, request):
        config = request.session.get("config_inventario_tipos_refaccion", {})
        visibles = config.get("columnas", ["nombre", "descripcion"])
        todas_las = ["nombre", "descripcion"]

        try:
            res = SESSION.get(f"{API_URL}/v1/tipos-refaccion/list/", timeout=8)
            if res.status_code != 200:
                raise requests.exceptions.RequestException
            tipos = res.json()
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el API.")
            tipos = []

        context = {
            "config": config,
            "tipos": tipos,
            "columnas": visibles,
            "todas_las_columnas": todas_las,
            "seccion": "inventario",
            "subseccion": "tipos_refaccion",
            "base_template": _base_template(request),
        }
        return render(request, self.template_name, context)


class CrearTipoRefaccion(generic.View):
    template_name = "inventario/crear_tipo_refaccion.html"

    def get(self, request):
        context = {
            "seccion": "inventario",
            "subseccion": "crear_tipo_refaccion",
            "base_template": _base_template(request),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        payload = {
            "nombre": request.POST.get("nombre"),
            "descripcion": request.POST.get("descripcion"),
        }
        try:
            res = SESSION.post(f"{API_URL}/v2/tipos-refaccion/create/", json=payload, timeout=10)
            if res.status_code == 201:
                messages.success(request, "Tipo de refacción creado correctamente.")
                return redirect("inventario:lista_tipos_refaccion")
            else:
                messages.error(request, f"Error: {res.json().get('detail', 'No se pudo crear el tipo.')}")
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el API.")
        return redirect("inventario:crear_tipo_refaccion")


class ProveedorModalView(generic.View):
    """Devuelve fragmento HTML con los datos de un proveedor."""

    def get(self, request, pk):
        proveedor = None
        try:
            res = SESSION.get(f"{API_URL}/v1/proveedores/{pk}/", timeout=5)
            if res.status_code == 200:
                proveedor = res.json()
        except requests.exceptions.RequestException:
            pass
        return render(request, "inventario/modal-proveedor.html", {"proveedor": proveedor})


class ExistenciaModalView(generic.View):
    """Devuelve fragmento HTML con la existencia de una refacción por estado."""

    def get(self, request, refaccion_id):
        existencias = []
        try:
            res = SESSION.get(f"{API_URL}/v1/existencia-refaccion/list/", timeout=5)
            if res.status_code == 200:
                existencias = [
                    e for e in res.json()
                    if e.get("refaccion") == refaccion_id
                ]
        except requests.exceptions.RequestException:
            pass
        return render(request, "inventario/modal-existencia.html", {"existencias": existencias})


class PiezaDepreciacionProxy(generic.View):
    """Reenvia POST /inventario/piezas/<numeroSerie>/depreciacion/ al api/
    (SP 5: sp_calcular_depreciacion_pieza). El drawer de piezas la llama
    por fetch() para calcular y guardar la depreciacion anual."""

    def post(self, request, numeroserie):
        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"detail": "JSON inválido."}, status=400)

        try:
            respuesta = SESSION.post(
                f"{API_URL}/v2/piezas/{numeroserie}/depreciacion/",
                json=payload,
                timeout=10,
            )
        except requests.exceptions.RequestException:
            return JsonResponse({"detail": "No fue posible conectar con el API."}, status=502)

        try:
            data = respuesta.json()
        except ValueError:
            data = {"detail": "Respuesta inválida del API."}
        return JsonResponse(data, status=respuesta.status_code, safe=False)