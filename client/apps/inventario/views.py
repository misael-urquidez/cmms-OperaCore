import requests
from collections import defaultdict
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.views import generic

from apps.gestion.registry import get_tabla

API_URL = f"{settings.API_BASE_URL}/inventario"

# Sesion HTTP a nivel de modulo: reusa la conexion TCP con el api/.
SESSION = requests.Session()

# Constantes de tiempo de vida en caché
PING_TTL = 30
CATALOGOS_TTL = 60 * 5   # 5 minutos para catálogos estáticos
INVENTARIO_TTL = 15      # 15 segundos para listas operativas


def _base_template(request):
    usuario = request.session.get("usuario", {})
    return "base_tecni.html" if usuario.get("rol") == "TECNI" else "base_admin.html"


MAX_COLUMNAS = 7


def _columnas_visibles(config):
    """Replica la lógica de GestionListView:选取 columnas visibles y si necesita modal."""
    todas_las = [c for c in config["campos"] if c.get("tipo") not in ("password", "file")]
    todas_las_con_archivos = [c for c in config["campos"] if c.get("tipo") != "password"]

    requeridos = [c for c in todas_las if c.get("requerido")]
    opcionales = [c for c in todas_las if not c.get("requerido")]
    restantes = MAX_COLUMNAS - len(requeridos[:MAX_COLUMNAS])
    visibles = requeridos[:MAX_COLUMNAS] + opcionales[:restantes]

    tiene_imagen = any(c.get("tipo") == "file" for c in config["campos"])
    necesita_modal = len(todas_las) > MAX_COLUMNAS or tiene_imagen

    return todas_las_con_archivos, visibles, necesita_modal


def _cargar_catalogos():
    catalogos = cache.get("inventario_catalogos")
    if catalogos:
        return catalogos, True

    try:
        response = SESSION.get(f"{API_URL}/v1/catalogos/", timeout=5)
        if response.status_code == 200:
            catalogos = response.json()
            cache.set("inventario_catalogos", catalogos, CATALOGOS_TTL)
            return catalogos, True
    except requests.exceptions.RequestException:
        pass

    return {}, False


# ------------ INDEX / PING -------------------------------------------------
class Index(generic.View):
    """Redirige al listado de piezas."""

    def get(self, request):
        return redirect("inventario:lista_piezas")


# ------------ REFACCIONES --------------------------------------------------
class ListaRefacciones(generic.View):
    template_name = "inventario/lista_refacciones.html"

    def get(self, request):
        config = get_tabla("refaccion")

        registros = cache.get("inventario_refacciones_list")
        if registros is None:
            try:
                res = SESSION.get(f"{API_URL}/v1/refacciones/list/", timeout=5)
                registros = res.json() if res.status_code == 200 else []
                cache.set("inventario_refacciones_list", registros, INVENTARIO_TTL)
            except requests.exceptions.RequestException:
                registros = []
                messages.warning(request, "Error de conexión con la API al cargar refacciones.")

        todas_las, visibles, necesita_modal = _columnas_visibles(config)

        reorden = sum(
            1 for r in registros
            if r.get("puntoreorden") and (r.get("stock") or 0) <= r["puntoreorden"]
        )
        stock_bajo = sum(
            1 for r in registros
            if (r.get("stock") or 0) < (r.get("stockminimo") or 0)
        )
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
            "columnas": visibles,
            "todas_las_columnas": todas_las,
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
            "codigoinventario": request.POST.get("codigoinventario"),
            "numeroorden": request.POST.get("numeroorden"),
            "costo": request.POST.get("costo"),
            "tiempoentregaapr": request.POST.get("tiempoentregaapr"),
            "stock": request.POST.get("stock"),
            "stockminimo": request.POST.get("stockminimo"),
            "proveedor": request.POST.get("proveedor"),
            "tipo_refaccion": request.POST.get("tipo_refaccion"),
            "clasificacion": request.POST.get("clasificacion"),
        }

        try:
            res = SESSION.post(f"{API_URL}/v2/refacciones/create/", data=payload, timeout=10)
            if res.status_code == 201:
                cache.delete("inventario_refacciones_list")
                messages.success(request, "Refacción registrada exitosamente.")
                return redirect("inventario:lista_refacciones")
            else:
                messages.warning(request, "Error al registrar la refacción. Revisa los campos.")
        except requests.exceptions.RequestException:
            messages.warning(request, "No se pudo conectar con el servidor.")

        catalogos, _ = _cargar_catalogos()
        return render(request, self.template_name, {
            "catalogos": catalogos,
            "seccion": "inventario",
            "subseccion": "crear_refaccion",
            "base_template": _base_template(request),
            "datos": dict(request.POST),
        })


# ------------ PIEZAS -------------------------------------------------------
class ListaPiezas(generic.View):
    template_name = "inventario/lista_pieza.html"

    def get(self, request):
        config = get_tabla("pieza")

        registros = cache.get("inventario_piezas_list")
        if registros is None:
            try:
                res = SESSION.get(f"{API_URL}/v1/piezas/list/", timeout=5)
                registros = res.json() if res.status_code == 200 else []
                cache.set("inventario_piezas_list", registros, INVENTARIO_TTL)
            except requests.exceptions.RequestException:
                registros = []
                messages.warning(request, "Error de conexión con la API al cargar piezas.")

        todas_las, visibles, necesita_modal = _columnas_visibles(config)

        maquinas = cache.get("inventario_maquinas_list")
        if maquinas is None:
            try:
                res_maq = SESSION.get(
                    f"{settings.API_BASE_URL}/maquinaria/v1/maquina/list/",
                    timeout=5,
                )
                maquinas = res_maq.json() if res_maq.status_code == 200 else []
                cache.set("inventario_maquinas_list", maquinas, INVENTARIO_TTL)
            except requests.exceptions.RequestException:
                maquinas = []

        maquinas_con_piezas = defaultdict(list)
        for reg in registros:
            maq_codigo = reg.get("maquina")
            if maq_codigo:
                maquinas_con_piezas[maq_codigo].append(reg)

        for codigo_maq, piezas in maquinas_con_piezas.items():
            for p in piezas:
                fecha_inst = p.get("fechainstalacion", "")
                try:
                    res_wear = SESSION.get(
                        f"{API_URL}/v1/piezas/wear/",
                        params={"maquina": codigo_maq, "fecha_instalacion": fecha_inst},
                        timeout=5,
                    )
                    wear_data = res_wear.json() if res_wear.status_code == 200 else {}
                except requests.exceptions.RequestException:
                    wear_data = {}

                horas_op = wear_data.get("horas_operacion", 0)
                vida = p.get("tiempovidautil") or 1
                p["porcentaje_desgaste"] = round(min(horas_op / vida * 100, 100), 1) if vida else 0

                costo = p.get("costoinicial") or 0
                residual = p.get("valorresidual") or 0
                vida_horas = p.get("tiempovidautil") or 1
                vida_anios = vida_horas / (22 * 8 * 12)
                p["depreciacion_anual"] = round((costo - residual) / vida_anios, 2) if vida_anios else 0

        from datetime import date as _date
        _hoy = _date.today()
        activas = sum(1 for p in registros if p.get("edo_pieza") == "OPERA")
        desgaste_alto = sum(1 for p in registros if p.get("porcentaje_desgaste", 0) > 85)
        garantia = sum(
            1 for p in registros
            if p.get("fechagarantia") and p["fechagarantia"] >= _hoy.isoformat()
        )
        rehabilitacion = sum(1 for p in registros if p.get("edo_pieza") == "ENREH")

        catalogos, _ = _cargar_catalogos()
        estados_pieza = catalogos.get("estados_pieza", [])
        tipos_pieza = catalogos.get("tipos_pieza", [])

        context = {
            "config": config,
            "registros": registros,
            "columnas": visibles,
            "todas_las_columnas": todas_las,
            "necesita_modal": necesita_modal,
            "seccion": "inventario",
            "subseccion": "piezas",
            "base_template": _base_template(request),
            "maquinas": maquinas,
            "maquinas_con_piezas": dict(maquinas_con_piezas),
            "kpi_activas": activas,
            "kpi_desgaste_alto": desgaste_alto,
            "kpi_garantia": garantia,
            "kpi_rehabilitacion": rehabilitacion,
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

        context = {
            "catalogos": catalogos,
            "seccion": "inventario",
            "subseccion": "crear_pieza",
            "base_template": _base_template(request),
        }
        return render(request, self.template_name, context)
 
    def post(self, request):
        payload = {
            "numeroserie": request.POST.get("numeroserie"),
            "codigoetiqueta": request.POST.get("codigoetiqueta"),
            "nombre": request.POST.get("nombre"),
            "costoinicial": request.POST.get("costoinicial"),
            "horasoperacion": request.POST.get("horasoperacion") or 0,
            "tiempovidautil": request.POST.get("tiempovidautil"),
            "depresacionanual": request.POST.get("depresacionanual") or 0,
            "valorresidual": request.POST.get("valorresidual") or 0,
            "fechainstalacion": request.POST.get("fechainstalacion") or None,
            "fechagarantia": request.POST.get("fechagarantia") or None,
            "edo_pieza": request.POST.get("edo_pieza"),
            "maquina": request.POST.get("maquina"),
            "tipo_pieza": request.POST.get("tipo_pieza"),
        }

        try:
            res = SESSION.post(f"{API_URL}/v2/piezas/create/", data=payload, timeout=10)
            if res.status_code == 201:
                cache.delete("inventario_piezas_list")
                messages.success(request, "Pieza registrada exitosamente.")
                return redirect("inventario:lista_piezas")
            else:
                messages.warning(request, "Error al registrar la pieza. Verifica los datos.")
        except requests.exceptions.RequestException:
            messages.warning(request, "No se pudo conectar con el servidor API.")

        catalogos, _ = _cargar_catalogos()
        return render(request, self.template_name, {
            "catalogos": catalogos,
            "seccion": "inventario",
            "subseccion": "crear_pieza",
            "base_template": _base_template(request),
            "datos": dict(request.POST),
        })


# ------------ HERRAMIENTAS --------------------------------------------------
class ListaHerramientas(generic.View):
    template_name = "inventario/lista_herramientas.html"

    def get(self, request):
        herramientas = cache.get("inventario_herramientas_list")
        if herramientas is None:
            try:
                res = SESSION.get(f"{API_URL}/v1/herramientas/list/", timeout=5)
                herramientas = res.json() if res.status_code == 200 else []
                cache.set("inventario_herramientas_list", herramientas, INVENTARIO_TTL)
            except requests.exceptions.RequestException:
                herramientas = []
                messages.warning(request, "Error al conectar con la API de herramientas.")

        context = {
            "herramientas": herramientas,
            "seccion": "inventario",
            "subseccion": "herramientas",
            "base_template": _base_template(request),
        }
        return render(request, self.template_name, context)


class CrearHerramienta(generic.View):
    template_name = "inventario/crear_herramienta.html"

    def get(self, request):
        catalogos, ok = _cargar_catalogos()
        if not ok:
            messages.warning(request, "No se pudieron obtener los catálogos del servidor.")

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
            "descripcion": request.POST.get("descripcion"),
            "tipo_herramienta": request.POST.get("tipo_herramienta"),
        }

        archivo = request.FILES.get("imagen")
        files = {"imagen": archivo} if archivo else None

        try:
            res = SESSION.post(f"{API_URL}/v2/herramientas/create/", data=payload, files=files, timeout=10)
            if res.status_code == 201:
                cache.delete("inventario_herramientas_list")
                messages.success(request, "Herramienta registrada exitosamente.")
                return redirect("inventario:lista_herramientas")
            else:
                messages.warning(request, "Error al registrar la herramienta.")
        except requests.exceptions.RequestException:
            messages.warning(request, "No se pudo establecer comunicación con el servicio.")

        catalogos, _ = _cargar_catalogos()
        return render(request, self.template_name, {
            "catalogos": catalogos,
            "seccion": "inventario",
            "subseccion": "crear_herramienta",
            "base_template": _base_template(request),
            "datos": dict(request.POST),
        })


# ------------ MOVIMIENTOS --------------------------------------------------
class ListaMovimientos(generic.View):
    template_name = "inventario/lista_movimientos.html"

    def get(self, request):
        registros = cache.get("inventario_movimientos_list")
        if registros is None:
            try:
                res = SESSION.get(
                    f"{settings.API_BASE_URL}/mantenimiento/v1/movimientos/list/",
                    timeout=5,
                )
                registros = res.json() if res.status_code == 200 else []
                cache.set("inventario_movimientos_list", registros, INVENTARIO_TTL)
            except requests.exceptions.RequestException:
                registros = []
                messages.warning(request, "Error de conexión con la API al cargar movimientos.")

        tipos_movimiento = cache.get("inventario_tipos_movimiento_list")
        if tipos_movimiento is None:
            try:
                res_tipo = SESSION.get(
                    f"{settings.API_BASE_URL}/mantenimiento/v1/tipo-movimiento/list/",
                    timeout=5,
                )
                tipos_movimiento = res_tipo.json() if res_tipo.status_code == 200 else []
                cache.set("inventario_tipos_movimiento_list", tipos_movimiento, CATALOGOS_TTL)
            except requests.exceptions.RequestException:
                tipos_movimiento = []

        context = {
            "registros": registros,
            "tipos_movimiento": tipos_movimiento,
            "seccion": "inventario",
            "subseccion": "movimientos",
            "base_template": _base_template(request),
        }
        return render(request, self.template_name, context)


class CrearMovimiento(generic.View):
    template_name = "inventario/crear_movimiento.html"

    API_BASE = settings.API_BASE_URL

    def _cargar_dropdowns(self):
        dropdowns = {}
        endpoints = {
            "ordenes": "/mantenimiento/v1/ordenes/list/",
            "piezas": "/inventario/v1/piezas/list/",
            "refacciones": "/inventario/v1/refacciones/list/",
            "tipos_movimiento": "/mantenimiento/v1/tipo-movimiento/list/",
            "tipos_pieza": "/inventario/v1/tipos-pieza/list/",
            "estados_pieza": "/inventario/v1/estados-pieza/list/",
            "maquinas": "/maquinaria/v1/maquina/list/",
        }
        for key, path in endpoints.items():
            try:
                res = SESSION.get(f"{self.API_BASE}{path}", timeout=5)
                dropdowns[key] = res.json() if res.status_code == 200 else []
            except requests.exceptions.RequestException:
                dropdowns[key] = []
        return dropdowns

    def get(self, request):
        dropdowns = self._cargar_dropdowns()
        datos = {}
        folio = request.GET.get("orden")
        if folio:
            datos["orden_mantenimiento"] = folio
        return render(request, self.template_name, {
            **dropdowns,
            "datos": datos,
            "seccion": "inventario",
            "subseccion": "movimientos",
            "base_template": _base_template(request),
        })

    def post(self, request):
        payload = {
            "tipoMovimiento": request.POST["tipoMovimiento"],
            "fecha": request.POST["fecha"],
            "hora": request.POST["hora"],
            "descripcion": request.POST.get("descripcion", ""),
            "orden_mantenimiento": request.POST.get("orden_mantenimiento") or None,
            "pieza": request.POST.get("pieza") or None,
            "refaccion": request.POST.get("refaccion") or None,
        }

        # Pieza nueva registrada desde el modal: la pieza "nace" al instalarse.
        # Se manda pieza_data para que el API la cree en transaccion con el
        # movimiento y registre pieza_id en la fila del MOVIMIENTO.
        campos_pieza = [
            "numeroserie", "codigoetiqueta", "nombre", "costoinicial",
            "horasoperacion", "tiempovidautil", "depresacionanual",
            "valorresidual", "fechainstalacion", "fechagarantia",
            "edo_pieza", "maquina", "tipo_pieza",
        ]
        pieza_nueva = {}
        for campo in campos_pieza:
            valor = request.POST.get(f"pieza_{campo}")
            if valor not in (None, ""):
                pieza_nueva[campo] = valor
        if pieza_nueva:
            payload["pieza_data"] = pieza_nueva
            payload.pop("pieza", None)

        try:
            res = SESSION.post(
                f"{self.API_BASE}/mantenimiento/v2/movimientos/create/",
                json=payload, timeout=10,
            )
            if res.status_code == 201:
                cache.delete("inventario_movimientos_list")
                messages.success(request, "Movimiento registrado exitosamente.")
                return redirect("inventario:lista_movimientos")
            else:
                messages.warning(request, "Error al registrar el movimiento.")
        except requests.exceptions.RequestException:
            messages.warning(request, "No se pudo establecer comunicación con la API.")
        dropdowns = self._cargar_dropdowns()
        return render(request, self.template_name, {
            **dropdowns,
            "seccion": "inventario",
            "subseccion": "movimientos",
            "base_template": _base_template(request),
            "datos": dict(request.POST),
        })


# ------------ PROVEEDORES --------------------------------------------------
class ListaProveedores(generic.View):
    template_name = "inventario/lista_proveedores.html"

    def get(self, request):
        proveedores = cache.get("inventario_proveedores_list")
        if proveedores is None:
            try:
                res = SESSION.get(f"{API_URL}/v1/proveedores/list/", timeout=5)
                proveedores = res.json() if res.status_code == 200 else []
                cache.set("inventario_proveedores_list", proveedores, CATALOGOS_TTL)
            except requests.exceptions.RequestException:
                proveedores = []
                messages.warning(request, "Error de conexión al cargar la lista de proveedores.")

        context = {
            "proveedores": proveedores,
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
            "rfc": request.POST.get("rfc"),
            "razonsocial": request.POST.get("razonsocial"),
            "direccion": request.POST.get("direccion"),
            "telefono": request.POST.get("telefono"),
            "email": request.POST.get("email"),
        }

        try:
            res = SESSION.post(f"{API_URL}/v2/proveedores/create/", data=payload, timeout=10)
            if res.status_code == 201:
                cache.delete("inventario_proveedores_list")
                cache.delete("inventario_catalogos")
                messages.success(request, "Proveedor registrado correctamente.")
                return redirect("inventario:lista_proveedores")
            else:
                messages.warning(request, "Error al registrar el proveedor. Verifica los datos.")
        except requests.exceptions.RequestException:
            messages.warning(request, "No se pudo comunicar con el servidor API.")

        return render(request, self.template_name, {
            "seccion": "inventario",
            "subseccion": "crear_proveedor",
            "base_template": _base_template(request),
            "datos": dict(request.POST),
        })


# ------------ CLASIFICACIONES ----------------------------------------------
class ListaClasificaciones(generic.View):
    template_name = "inventario/lista_clasificaciones.html"

    def get(self, request):
        clasificaciones = cache.get("inventario_clasificaciones_list")
        if clasificaciones is None:
            try:
                res = SESSION.get(f"{API_URL}/v1/clasificaciones/list/", timeout=5)
                clasificaciones = res.json() if res.status_code == 200 else []
                cache.set("inventario_clasificaciones_list", clasificaciones, CATALOGOS_TTL)
            except requests.exceptions.RequestException:
                clasificaciones = []
                messages.warning(request, "Error al conectar con la API de clasificaciones.")

        context = {
            "clasificaciones": clasificaciones,
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
            "clave": request.POST.get("clave"),
            "nombre": request.POST.get("nombre"),
            "descripcion": request.POST.get("descripcion"),
        }

        try:
            res = SESSION.post(f"{API_URL}/v2/clasificaciones/create/", data=payload, timeout=10)
            if res.status_code == 201:
                cache.delete("inventario_clasificaciones_list")
                cache.delete("inventario_catalogos")
                messages.success(request, "Clasificación creada con éxito.")
                return redirect("inventario:lista_clasificaciones")
            else:
                messages.warning(request, "No se pudo crear la clasificación.")
        except requests.exceptions.RequestException:
            messages.warning(request, "Error de comunicación con el servicio.")

        return render(request, self.template_name, {
            "seccion": "inventario",
            "subseccion": "crear_clasificacion",
            "base_template": _base_template(request),
            "datos": dict(request.POST),
        })


# ------------ ESTADOS (HERRAMIENTA, PIEZA, REFACCIÓN) --------------------
class ListaEstadosHerramienta(generic.View):
    template_name = "inventario/lista_estados_herramienta.html"

    def get(self, request):
        estados = cache.get("inventario_estados_herramienta_list")
        if estados is None:
            try:
                res = SESSION.get(f"{API_URL}/v1/estados-herramienta/list/", timeout=5)
                estados = res.json() if res.status_code == 200 else []
                cache.set("inventario_estados_herramienta_list", estados, CATALOGOS_TTL)
            except requests.exceptions.RequestException:
                estados = []
                messages.warning(request, "Error al cargar estados de herramienta.")

        return render(request, self.template_name, {"estados": estados, "seccion": "inventario", "subseccion": "estados_herramienta", "base_template": _base_template(request)})


class CrearEstadoHerramienta(generic.View):
    template_name = "inventario/crear_estado_herramienta.html"

    def get(self, request):
        return render(request, self.template_name, {"seccion": "inventario", "subseccion": "crear_estado_herramienta", "base_template": _base_template(request)})

    def post(self, request):
        payload = {"clave": request.POST.get("clave"), "nombre": request.POST.get("nombre")}
        try:
            res = SESSION.post(f"{API_URL}/v2/estados-herramienta/create/", data=payload, timeout=10)
            if res.status_code == 201:
                cache.delete("inventario_estados_herramienta_list")
                cache.delete("inventario_catalogos")
                messages.success(request, "Estado de herramienta registrado.")
                return redirect("inventario:lista_estados_herramienta")
            else:
                messages.warning(request, "Error al registrar el estado de herramienta.")
        except requests.exceptions.RequestException:
            messages.warning(request, "Error de red con la API.")
        return render(request, self.template_name, {"seccion": "inventario", "subseccion": "crear_estado_herramienta", "base_template": _base_template(request), "datos": dict(request.POST)})


class ListaEstadosPieza(generic.View):
    template_name = "inventario/lista_estados_pieza.html"

    def get(self, request):
        estados = cache.get("inventario_estados_pieza_list")
        if estados is None:
            try:
                res = SESSION.get(f"{API_URL}/v1/estados-pieza/list/", timeout=5)
                estados = res.json() if res.status_code == 200 else []
                cache.set("inventario_estados_pieza_list", estados, CATALOGOS_TTL)
            except requests.exceptions.RequestException:
                estados = []
                messages.warning(request, "Error al cargar estados de pieza.")

        return render(request, self.template_name, {"estados": estados, "seccion": "inventario", "subseccion": "estados_pieza", "base_template": _base_template(request)})


class CrearEstadoPieza(generic.View):
    template_name = "inventario/crear_estado_pieza.html"

    def get(self, request):
        return render(request, self.template_name, {"seccion": "inventario", "subseccion": "crear_estado_pieza", "base_template": _base_template(request)})

    def post(self, request):
        payload = {"clave": request.POST.get("clave"), "nombre": request.POST.get("nombre")}
        try:
            res = SESSION.post(f"{API_URL}/v2/estados-pieza/create/", data=payload, timeout=10)
            if res.status_code == 201:
                cache.delete("inventario_estados_pieza_list")
                cache.delete("inventario_catalogos")
                messages.success(request, "Estado de pieza registrado.")
                return redirect("inventario:lista_estados_pieza")
            else:
                messages.warning(request, "Error al registrar el estado de pieza.")
        except requests.exceptions.RequestException:
            messages.warning(request, "Error de red con la API.")
        return render(request, self.template_name, {"seccion": "inventario", "subseccion": "crear_estado_pieza", "base_template": _base_template(request), "datos": dict(request.POST)})


class ListaEstadosRefaccion(generic.View):
    template_name = "inventario/lista_estados_refaccion.html"

    def get(self, request):
        estados = cache.get("inventario_estados_refaccion_list")
        if estados is None:
            try:
                res = SESSION.get(f"{API_URL}/v1/estados-refaccion/list/", timeout=5)
                estados = res.json() if res.status_code == 200 else []
                cache.set("inventario_estados_refaccion_list", estados, CATALOGOS_TTL)
            except requests.exceptions.RequestException:
                estados = []
                messages.warning(request, "Error al cargar estados de refacción.")

        return render(request, self.template_name, {"estados": estados, "seccion": "inventario", "subseccion": "estados_refaccion", "base_template": _base_template(request)})


class CrearEstadoRefaccion(generic.View):
    template_name = "inventario/crear_estado_refaccion.html"

    def get(self, request):
        return render(request, self.template_name, {"seccion": "inventario", "subseccion": "crear_estado_refaccion", "base_template": _base_template(request)})

    def post(self, request):
        payload = {"clave": request.POST.get("clave"), "nombre": request.POST.get("nombre")}
        try:
            res = SESSION.post(f"{API_URL}/v2/estados-refaccion/create/", data=payload, timeout=10)
            if res.status_code == 201:
                cache.delete("inventario_estados_refaccion_list")
                cache.delete("inventario_catalogos")
                messages.success(request, "Estado de refacción registrado.")
                return redirect("inventario:lista_estados_refaccion")
            else:
                messages.warning(request, "Error al registrar el estado de refacción.")
        except requests.exceptions.RequestException:
            messages.warning(request, "Error de red con la API.")
        return render(request, self.template_name, {"seccion": "inventario", "subseccion": "crear_estado_refaccion", "base_template": _base_template(request), "datos": dict(request.POST)})


# ------------ TIPOS (HERRAMIENTA, PIEZA, REFACCIÓN) ----------------------
class ListaTiposHerramienta(generic.View):
    template_name = "inventario/lista_tipos_herramienta.html"

    def get(self, request):
        tipos = cache.get("inventario_tipos_herramienta_list")
        if tipos is None:
            try:
                res = SESSION.get(f"{API_URL}/v1/tipos-herramienta/list/", timeout=5)
                tipos = res.json() if res.status_code == 200 else []
                cache.set("inventario_tipos_herramienta_list", tipos, CATALOGOS_TTL)
            except requests.exceptions.RequestException:
                tipos = []
                messages.warning(request, "Error al cargar tipos de herramienta.")

        return render(request, self.template_name, {"tipos": tipos, "seccion": "inventario", "subseccion": "tipos_herramienta", "base_template": _base_template(request)})


class CrearTipoHerramienta(generic.View):
    template_name = "inventario/crear_tipo_herramienta.html"

    def get(self, request):
        return render(request, self.template_name, {"seccion": "inventario", "subseccion": "crear_tipo_herramienta", "base_template": _base_template(request)})

    def post(self, request):
        payload = {"nombre": request.POST.get("nombre"), "descripcion": request.POST.get("descripcion")}
        try:
            res = SESSION.post(f"{API_URL}/v2/tipos-herramienta/create/", data=payload, timeout=10)
            if res.status_code == 201:
                cache.delete("inventario_tipos_herramienta_list")
                cache.delete("inventario_catalogos")
                messages.success(request, "Tipo de herramienta creado.")
                return redirect("inventario:lista_tipos_herramienta")
            else:
                messages.warning(request, "Error al crear el tipo de herramienta.")
        except requests.exceptions.RequestException:
            messages.warning(request, "Error de conexión con la API.")
        return render(request, self.template_name, {"seccion": "inventario", "subseccion": "crear_tipo_herramienta", "base_template": _base_template(request), "datos": dict(request.POST)})


class ListaTiposPieza(generic.View):
    template_name = "inventario/lista_tipos_pieza.html"

    def get(self, request):
        tipos = cache.get("inventario_tipos_pieza_list")
        if tipos is None:
            try:
                res = SESSION.get(f"{API_URL}/v1/tipos-pieza/list/", timeout=5)
                tipos = res.json() if res.status_code == 200 else []
                cache.set("inventario_tipos_pieza_list", tipos, CATALOGOS_TTL)
            except requests.exceptions.RequestException:
                tipos = []
                messages.warning(request, "Error al cargar tipos de pieza.")

        return render(request, self.template_name, {"tipos": tipos, "seccion": "inventario", "subseccion": "tipos_pieza", "base_template": _base_template(request)})


class CrearTipoPieza(generic.View):
    template_name = "inventario/crear_tipo_pieza.html"

    def get(self, request):
        return render(request, self.template_name, {"seccion": "inventario", "subseccion": "crear_tipo_pieza", "base_template": _base_template(request)})

    def post(self, request):
        payload = {"nombre": request.POST.get("nombre"), "descripcion": request.POST.get("descripcion")}
        try:
            res = SESSION.post(f"{API_URL}/v2/tipos-pieza/create/", data=payload, timeout=10)
            if res.status_code == 201:
                cache.delete("inventario_tipos_pieza_list")
                cache.delete("inventario_catalogos")
                messages.success(request, "Tipo de pieza creado.")
                return redirect("inventario:lista_tipos_pieza")
            else:
                messages.warning(request, "Error al crear el tipo de pieza.")
        except requests.exceptions.RequestException:
            messages.warning(request, "Error de conexión con la API.")
        return render(request, self.template_name, {"seccion": "inventario", "subseccion": "crear_tipo_pieza", "base_template": _base_template(request), "datos": dict(request.POST)})


class ListaTiposRefaccion(generic.View):
    template_name = "inventario/lista_tipos_refaccion.html"

    def get(self, request):
        tipos = cache.get("inventario_tipos_refaccion_list")
        if tipos is None:
            try:
                res = SESSION.get(f"{API_URL}/v1/tipos-refaccion/list/", timeout=5)
                tipos = res.json() if res.status_code == 200 else []
                cache.set("inventario_tipos_refaccion_list", tipos, CATALOGOS_TTL)
            except requests.exceptions.RequestException:
                tipos = []
                messages.warning(request, "Error al cargar tipos de refacción.")

        return render(request, self.template_name, {"tipos": tipos, "seccion": "inventario", "subseccion": "tipos_refaccion", "base_template": _base_template(request)})


class CrearTipoRefaccion(generic.View):
    template_name = "inventario/crear_tipo_refaccion.html"

    def get(self, request):
        return render(request, self.template_name, {"seccion": "inventario", "subseccion": "crear_tipo_refaccion", "base_template": _base_template(request)})

    def post(self, request):
        payload = {"nombre": request.POST.get("nombre"), "descripcion": request.POST.get("descripcion")}
        try:
            res = SESSION.post(f"{API_URL}/v2/tipos-refaccion/create/", data=payload, timeout=10)
            if res.status_code == 201:
                cache.delete("inventario_tipos_refaccion_list")
                cache.delete("inventario_catalogos")
                messages.success(request, "Tipo de refacción creado.")
                return redirect("inventario:lista_tipos_refaccion")
            else:
                messages.warning(request, "Error al crear el tipo de refacción.")
        except requests.exceptions.RequestException:
            messages.warning(request, "Error de conexión con la API.")
        return render(request, self.template_name, {"seccion": "inventario", "subseccion": "crear_tipo_refaccion", "base_template": _base_template(request), "datos": dict(request.POST)})


# ------------ MODALES (fragmentos HTML) ------------------------------------

class ProveedorModalView(generic.View):
    """Devuelve fragmento HTML con el detalle del proveedor para el modal."""

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
                    if e.get("refaccion") == int(refaccion_id)
                ]
        except requests.exceptions.RequestException:
            pass

        estados_map = {}
        try:
            res_edo = SESSION.get(f"{API_URL}/v1/estados-refaccion/list/", timeout=5)
            if res_edo.status_code == 200:
                estados_map = {e["codigo"]: e["nombre"] for e in res_edo.json()}
        except requests.exceptions.RequestException:
            pass

        return render(request, "inventario/modal-existencia.html", {
            "existencias": existencias,
            "estados_map": estados_map,
        })