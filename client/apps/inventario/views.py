import requests
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.views import generic

API_URL = f"{settings.API_BASE_URL}/inventario"

# Sesion HTTP a nivel de modulo: reusa la conexion TCP con el api/.
SESSION = requests.Session()

# Constantes de tiempo de vida en caché
PING_TTL = 30
CATALOGOS_TTL = 60 * 5   # 5 minutos para catálogos estáticos
INVENTARIO_TTL = 15      # 15 segundos para listas operativas


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
    """Pantalla principal del módulo Inventario. Consume el api/ por HTTP."""

    template_name = "inventario/index.html"

    def get(self, request):
        response = cache.get("inventario_ping")
        if response is None:
            try:
                response = SESSION.get(f"{API_URL}/ping/", timeout=5).json()
            except requests.exceptions.RequestException:
                response = {"status": "sin conexion con el api"}
            cache.set("inventario_ping", response, PING_TTL)
        return render(request, self.template_name, {"modulo": "Inventario", "api_status": response})


# ------------ REFACCIONES --------------------------------------------------
class ListaRefacciones(generic.View):
    template_name = "inventario/lista_refacciones.html"

    def get(self, request):
        refacciones = cache.get("inventario_refacciones_list")
        if refacciones is None:
            try:
                res = SESSION.get(f"{API_URL}/v1/refacciones/list/", timeout=5)
                refacciones = res.json() if res.status_code == 200 else []
                cache.set("inventario_refacciones_list", refacciones, INVENTARIO_TTL)
            except requests.exceptions.RequestException:
                refacciones = []
                messages.warning(request, "Error de conexión con la API al cargar refacciones.")

        context = {
            "refacciones": refacciones,
            "seccion": "inventario",
            "subseccion": "refacciones",
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

        return redirect("inventario:crear_refaccion")


# ------------ PIEZAS -------------------------------------------------------
class ListaPiezas(generic.View):
    template_name = "inventario/lista_piezas.html"

    def get(self, request):
        piezas = cache.get("inventario_piezas_list")
        if piezas is None:
            try:
                res = SESSION.get(f"{API_URL}/v1/piezas/list/", timeout=5)
                piezas = res.json() if res.status_code == 200 else []
                cache.set("inventario_piezas_list", piezas, INVENTARIO_TTL)
            except requests.exceptions.RequestException:
                piezas = []
                messages.warning(request, "Error de conexión con la API al cargar piezas.")

        context = {
            "piezas": piezas,
            "seccion": "inventario",
            "subseccion": "piezas",
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

        return redirect("inventario:crear_pieza")


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

        return redirect("inventario:crear_herramienta")


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
        }
        return render(request, self.template_name, context)


class CrearProveedor(generic.View):
    template_name = "inventario/crear_proveedor.html"

    def get(self, request):
        context = {
            "seccion": "inventario",
            "subseccion": "crear_proveedor",
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

        return redirect("inventario:crear_proveedor")


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
        }
        return render(request, self.template_name, context)


class CrearClasificacion(generic.View):
    template_name = "inventario/crear_clasificacion.html"

    def get(self, request):
        context = {
            "seccion": "inventario",
            "subseccion": "crear_clasificacion",
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

        return redirect("inventario:crear_clasificacion")


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

        return render(request, self.template_name, {"estados": estados, "seccion": "inventario", "subseccion": "estados_herramienta"})


class CrearEstadoHerramienta(generic.View):
    template_name = "inventario/crear_estado_herramienta.html"

    def get(self, request):
        return render(request, self.template_name, {"seccion": "inventario", "subseccion": "crear_estado_herramienta"})

    def post(self, request):
        payload = {"clave": request.POST.get("clave"), "nombre": request.POST.get("nombre")}
        try:
            res = SESSION.post(f"{API_URL}/v2/estados-herramienta/create/", data=payload, timeout=10)
            if res.status_code == 201:
                cache.delete("inventario_estados_herramienta_list")
                cache.delete("inventario_catalogos")
                messages.success(request, "Estado de herramienta registrado.")
                return redirect("inventario:lista_estados_herramienta")
        except requests.exceptions.RequestException:
            messages.warning(request, "Error de red con la API.")
        return redirect("inventario:crear_estado_herramienta")


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

        return render(request, self.template_name, {"estados": estados, "seccion": "inventario", "subseccion": "estados_pieza"})


class CrearEstadoPieza(generic.View):
    template_name = "inventario/crear_estado_pieza.html"

    def get(self, request):
        return render(request, self.template_name, {"seccion": "inventario", "subseccion": "crear_estado_pieza"})

    def post(self, request):
        payload = {"clave": request.POST.get("clave"), "nombre": request.POST.get("nombre")}
        try:
            res = SESSION.post(f"{API_URL}/v2/estados-pieza/create/", data=payload, timeout=10)
            if res.status_code == 201:
                cache.delete("inventario_estados_pieza_list")
                cache.delete("inventario_catalogos")
                messages.success(request, "Estado de pieza registrado.")
                return redirect("inventario:lista_estados_pieza")
        except requests.exceptions.RequestException:
            messages.warning(request, "Error de red con la API.")
        return redirect("inventario:crear_estado_pieza")


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

        return render(request, self.template_name, {"estados": estados, "seccion": "inventario", "subseccion": "estados_refaccion"})


class CrearEstadoRefaccion(generic.View):
    template_name = "inventario/crear_estado_refaccion.html"

    def get(self, request):
        return render(request, self.template_name, {"seccion": "inventario", "subseccion": "crear_estado_refaccion"})

    def post(self, request):
        payload = {"clave": request.POST.get("clave"), "nombre": request.POST.get("nombre")}
        try:
            res = SESSION.post(f"{API_URL}/v2/estados-refaccion/create/", data=payload, timeout=10)
            if res.status_code == 201:
                cache.delete("inventario_estados_refaccion_list")
                cache.delete("inventario_catalogos")
                messages.success(request, "Estado de refacción registrado.")
                return redirect("inventario:lista_estados_refaccion")
        except requests.exceptions.RequestException:
            messages.warning(request, "Error de red con la API.")
        return redirect("inventario:crear_estado_refaccion")


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

        return render(request, self.template_name, {"tipos": tipos, "seccion": "inventario", "subseccion": "tipos_herramienta"})


class CrearTipoHerramienta(generic.View):
    template_name = "inventario/crear_tipo_herramienta.html"

    def get(self, request):
        return render(request, self.template_name, {"seccion": "inventario", "subseccion": "crear_tipo_herramienta"})

    def post(self, request):
        payload = {"nombre": request.POST.get("nombre"), "descripcion": request.POST.get("descripcion")}
        try:
            res = SESSION.post(f"{API_URL}/v2/tipos-herramienta/create/", data=payload, timeout=10)
            if res.status_code == 201:
                cache.delete("inventario_tipos_herramienta_list")
                cache.delete("inventario_catalogos")
                messages.success(request, "Tipo de herramienta creado.")
                return redirect("inventario:lista_tipos_herramienta")
        except requests.exceptions.RequestException:
            messages.warning(request, "Error de conexión con la API.")
        return redirect("inventario:crear_tipo_herramienta")


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

        return render(request, self.template_name, {"tipos": tipos, "seccion": "inventario", "subseccion": "tipos_pieza"})


class CrearTipoPieza(generic.View):
    template_name = "inventario/crear_tipo_pieza.html"

    def get(self, request):
        return render(request, self.template_name, {"seccion": "inventario", "subseccion": "crear_tipo_pieza"})

    def post(self, request):
        payload = {"nombre": request.POST.get("nombre"), "descripcion": request.POST.get("descripcion")}
        try:
            res = SESSION.post(f"{API_URL}/v2/tipos-pieza/create/", data=payload, timeout=10)
            if res.status_code == 201:
                cache.delete("inventario_tipos_pieza_list")
                cache.delete("inventario_catalogos")
                messages.success(request, "Tipo de pieza creado.")
                return redirect("inventario:lista_tipos_pieza")
        except requests.exceptions.RequestException:
            messages.warning(request, "Error de conexión con la API.")
        return redirect("inventario:crear_tipo_pieza")


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

        return render(request, self.template_name, {"tipos": tipos, "seccion": "inventario", "subseccion": "tipos_refaccion"})


class CrearTipoRefaccion(generic.View):
    template_name = "inventario/crear_tipo_refaccion.html"

    def get(self, request):
        return render(request, self.template_name, {"seccion": "inventario", "subseccion": "crear_tipo_refaccion"})

    def post(self, request):
        payload = {"nombre": request.POST.get("nombre"), "descripcion": request.POST.get("descripcion")}
        try:
            res = SESSION.post(f"{API_URL}/v2/tipos-refaccion/create/", data=payload, timeout=10)
            if res.status_code == 201:
                cache.delete("inventario_tipos_refaccion_list")
                cache.delete("inventario_catalogos")
                messages.success(request, "Tipo de refacción creado.")
                return redirect("inventario:lista_tipos_refaccion")
        except requests.exceptions.RequestException:
            messages.warning(request, "Error de conexión con la API.")
        return redirect("inventario:crear_tipo_refaccion")