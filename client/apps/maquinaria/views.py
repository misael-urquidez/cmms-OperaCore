import re

import requests
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.shortcuts import render, redirect, get_object_or_404
from django.templatetags.static import static
from django.views import generic
from .forms import MaquinaForm
from django.views.generic import TemplateView

API_URL = f"{settings.API_BASE_URL}/maquinaria"

# Sesion HTTP a nivel de modulo: reusa la conexion TCP con la API
SESSION = requests.Session()

# Cache de 30 segundos para la verificacion de estado (ping)
PING_TTL = 30

# Prefijo con el que se autogenera el código si el usuario no captura uno.
CODIGO_PREFIJO = "MAQ"
CODIGO_RE = re.compile(rf"^{CODIGO_PREFIJO}(\d+)$")


class Index(generic.View):
    """Dashboard principal: Muestra métricas generales y el estado del servicio."""

    template_name = "maquinaria/index.html"

    def get(self, request):
        usuario = request.session.get("usuario")
        if not usuario:
            messages.warning(request, "Inicia sesión para continuar.")
            return redirect("usuarios:index")

        # 1. Obtener estado del servicio vía ping (usando caché)
        api_status = cache.get("maquinaria_ping")
        if api_status is None:
            try:
                res_ping = SESSION.get(f"{API_URL}/ping/", timeout=5)
                api_status = res_ping.json() if res_ping.status_code == 200 else {"status": "error"}
            except requests.exceptions.RequestException:
                api_status = {"status": "sin conexion con el api"}
            cache.set("maquinaria_ping", api_status, PING_TTL)

        # 2. Obtener la lista de máquinas
        try:
            res = SESSION.get(f"{API_URL}/v1/maquina/list/", timeout=5)
            maquinas = res.json() if res.status_code == 200 else []
        except requests.exceptions.RequestException:
            maquinas = []

        # El catálogo de estados se necesita ANTES de contar operativas: el
        # API regresa 'estado_maquina' como el código FK (p. ej. 'OPERA',
        # 'MANTE', 'FALLO'...), no como el nombre. Comparar el código
        # directo contra strings como "activo"/"operativa" nunca iba a
        # coincidir con nada -> el contador de operativos siempre daba 0.
        edos_maquina = cache.get("maquinaria_edos_list")
        if edos_maquina is None:
            try:
                res_edo = SESSION.get(f"{API_URL}/v1/edo_maquina/list/", timeout=5)
                edos_maquina = res_edo.json() if res_edo.status_code == 200 else []
                cache.set("maquinaria_edos_list", edos_maquina, 300)
            except requests.exceptions.RequestException:
                edos_maquina = []

        edo_dict = {e["codigo"]: e["nombre"] for e in edos_maquina if "codigo" in e}

        total_maquinas = len(maquinas)
        operativas = sum(
            1 for m in maquinas
            if edo_dict.get(m.get("estado_maquina"), "").strip().lower() == "operativa"
        )
        en_mantenimiento = total_maquinas - operativas

        lineas = cache.get("maquinaria_lineas_list")
        if lineas is None:
            try:
                res_lin = SESSION.get(f"{API_URL}/v1/linea/list/", timeout=5)
                lineas = res_lin.json() if res_lin.status_code == 200 else []
                cache.set("maquinaria_lineas_list", lineas, 300)
            except requests.exceptions.RequestException:
                lineas = []

        tipos_maquina = cache.get("maquinaria_tipos_list")
        if tipos_maquina is None:
            try:
                res_tip = SESSION.get(f"{API_URL}/v1/tipo_maquina/list/", timeout=5)
                tipos_maquina = res_tip.json() if res_tip.status_code == 200 else []
                cache.set("maquinaria_tipos_list", tipos_maquina, 300)
            except requests.exceptions.RequestException:
                tipos_maquina = []

        marcas = cache.get("maquinaria_marcas_list")
        if marcas is None:
            try:
                res_mar = SESSION.get(f"{API_URL}/v1/marca/list/", timeout=5)
                marcas = res_mar.json() if res_mar.status_code == 200 else []
                cache.set("maquinaria_marcas_list", marcas, 300)
            except requests.exceptions.RequestException:
                marcas = []

        modelos = cache.get("maquinaria_modelos_list")
        if modelos is None:
            try:
                res_mod = SESSION.get(f"{API_URL}/v1/modelo/list/", timeout=5)
                modelos = res_mod.json() if res_mod.status_code == 200 else []
                cache.set("maquinaria_modelos_list", modelos, 300)
            except requests.exceptions.RequestException:
                modelos = []

        linea_dict = {l["codigo"]: l["nombre"] for l in lineas if "codigo" in l}
        tipo_dict = {t.get("numeroregistro", t.get("codigo", "")): t["nombre"] for t in tipos_maquina if "nombre" in t}
        marca_dict = {m["clave"]: m["nombre"] for m in marcas if "clave" in m}
        modelo_dict = {m["codigo"]: m["nombre"] for m in modelos if "codigo" in m}

        context = {
            "modulo": "Maquinaria",
            "api_status": api_status,
            "maquinas": maquinas,
            "lineas": lineas,
            "edos_maquina": edos_maquina,
            "tipos_maquina": tipos_maquina,
            "marcas": marcas,
            "modelos": modelos,
            "linea_dict": linea_dict,
            "edo_dict": edo_dict,
            "tipo_dict": tipo_dict,
            "marca_dict": marca_dict,
            "modelo_dict": modelo_dict,
            "total_maquinas": total_maquinas,
            "operativas": operativas,
            "en_mantenimiento": en_mantenimiento,
            "usuario": usuario,
            "base_template": "base_tecni.html" if usuario.get("rol") == "TECNI" else "base_admin.html",
        }
        return render(request, self.template_name, context)


class ListarMaquinas(generic.View):
    """Catálogo tradicional en tarjetas detalladas."""

    template_name = "maquinaria/lista_maquinas.html"

    def get(self, request):
        try:
            res = SESSION.get(f"{API_URL}/v1/maquina/list/", timeout=5)
            data = res.json() if res.status_code == 200 else []
        except requests.exceptions.RequestException:
            data = []

        return render(request, self.template_name, {"maquinas": data})


def _resolver_media_url(ruta):
    """Las máquinas 'de catálogo' (datos de demo, cargados directo en BD)
    guardan una ruta relativa a static/maquinaria/ del cliente, por ejemplo
    'images/YamahaYS12.png'. Las máquinas dadas de alta desde el formulario
    (CrearMaquina) suben el archivo real, que el API guarda bajo su propio
    MEDIA_ROOT con una ruta que empieza con 'maquinaria/', por ejemplo
    'maquinaria/imagen_2026-08-01_164746369.png'.

    Son dos ubicaciones físicas distintas (estáticos del cliente vs. media
    del servidor API), así que hay que armar la URL absoluta distinta según
    el caso. Antes el template intentaba servir todo desde los estáticos del
    cliente, por lo que las fotos/modelos subidos de verdad salían rotos."""
    if not ruta or ruta == "None":
        return None
    if ruta.startswith("maquinaria/"):
        # Archivo real, servido por el API desde su propio MEDIA_ROOT.
        return f"{settings.API_ROOT_URL}/media/{ruta}"
    # Ruta de catálogo/demo, vive en los estáticos del cliente.
    return static(f"maquinaria/{ruta}")


class DetalleMaquina(generic.View):
    """Detalle técnico e individual de una máquina con su visor 3D."""

    template_name = "maquinaria/detalle_maquina.html"

    def get(self, request, codigo):
        url = f"{API_URL}/v1/maquina/{codigo}/"
        try:
            res = SESSION.get(url, timeout=5)
            data = res.json() if res.status_code == 200 else None
        except requests.exceptions.RequestException:
            data = None

        ubicacion = None
        if data and data.get("linea"):
            try:
                res_lin = SESSION.get(f"{API_URL}/v1/linea/list/", timeout=5)
                lineas = res_lin.json() if res_lin.status_code == 200 else []

                res_are = SESSION.get(f"{API_URL}/v1/area/list/", timeout=5)
                areas = res_are.json() if res_are.status_code == 200 else []

                res_pla = SESSION.get(f"{API_URL}/v1/planta/list/", timeout=5)
                plantas = res_pla.json() if res_pla.status_code == 200 else []

                linea = next((l for l in lineas if l.get("codigo") == data["linea"]), None)
                area = None
                planta = None
                if linea:
                    area = next((a for a in areas if a.get("codigo") == linea.get("area")), None)
                if area:
                    planta = next((p for p in plantas if p.get("codigo") == area.get("planta")), None)

                ubicacion = {
                    "linea": linea.get("nombre") if linea else None,
                    "area": area.get("nombre") if area else None,
                    "planta": planta.get("nombre") if planta else None,
                }
            except requests.exceptions.RequestException:
                ubicacion = None

        context = {
            "maquina": data,
            "ubicacion": ubicacion,
            "imagen_url_resuelta": _resolver_media_url(data.get("imagen_url")) if data else None,
            "modelo_3d_url_resuelta": _resolver_media_url(data.get("modelo_3d")) if data else None,
        }
        return render(request, self.template_name, context)


def _siguiente_codigo():
    """Autogenera MAQ001, MAQ002, ... tomando el máximo numérico existente
    (no la cantidad de máquinas: si se borró una a la mitad, contar por
    longitud produce códigos duplicados y el API los rechaza por PK
    repetida sin decir nada claro)."""
    try:
        res = SESSION.get(f"{API_URL}/v1/maquina/list/", timeout=5)
        existentes = res.json() if res.status_code == 200 else []
    except requests.exceptions.RequestException:
        existentes = []

    maximo = 0
    for m in existentes:
        match = CODIGO_RE.match(str(m.get("codigo", "")))
        if match:
            maximo = max(maximo, int(match.group(1)))
    return f"{CODIGO_PREFIJO}{maximo + 1:03d}"


def _detalle_error_api(response):
    """Convierte el JSON de error de DRF ({'campo': ['msg']}) en un texto
    legible para mostrarlo con messages.warning."""
    try:
        cuerpo = response.json()
    except ValueError:
        return f"El API respondió {response.status_code}."
    if isinstance(cuerpo, dict):
        partes = []
        for campo, errores in cuerpo.items():
            if isinstance(errores, list):
                errores = ", ".join(str(e) for e in errores)
            partes.append(f"{campo}: {errores}")
        return " | ".join(partes)
    return str(cuerpo)


class CrearMaquina(generic.View):
    template_name = "maquinaria/crear_maquina.html"

    def get(self, request):
        form = MaquinaForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = MaquinaForm(request.POST, request.FILES)

        if not form.is_valid():
            messages.warning(request, "Revisa los campos marcados en rojo.")
            return render(request, self.template_name, {"form": form})

        cleaned = form.cleaned_data

        # Payload de texto: solo se manda lo que sí tiene valor, para no
        # pisar con "" campos opcionales (numeroserie es UNIQUE en BD;
        # mandar "" en dos altas distintas choca contra ese unique).
        payload = {}
        for campo in ("numeroserie", "nombre", "descripcion", "linea",
                      "marca", "modelo", "estado_maquina", "tipo_maquina"):
            valor = cleaned.get(campo)
            if valor:
                payload[campo] = valor

        payload["codigo"] = cleaned.get("codigo") or _siguiente_codigo()
        payload["fechainstalacion"] = cleaned["fechainstalacion"].isoformat()

        files_payload = {}
        imagen = cleaned.get("imagen_url")
        if imagen:
            # El API espera la llave 'imagen' (FileField write-only del
            # serializer), NO 'imagen_url' (ese es el CharField donde el
            # API guarda la ruta ya procesada).
            files_payload["imagen"] = (imagen.name, imagen.read(), imagen.content_type)

        modelo_3d = cleaned.get("modelo_3d")
        if modelo_3d:
            # El API guarda esto en MEDIA_ROOT/maquinaria/modelos3d/ y
            # setea Maquina.modelo_3d con la ruta relativa (ver
            # apps/maquinaria/serializers.py -> CreateMaquinaSerializer
            # en el proyecto cmms).
            files_payload["modelo_3d_archivo"] = (modelo_3d.name, modelo_3d.read(), modelo_3d.content_type)

        try:
            response = SESSION.post(
                f"{API_URL}/v1/maquina/create/",
                data=payload,
                files=files_payload if files_payload else None,
                timeout=10,
            )
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el API de maquinaria.")
            return render(request, self.template_name, {"form": form})

        if response.status_code in (200, 201):
            for clave in ("maquinaria_lineas_list", "maquinaria_marcas_list",
                          "maquinaria_modelos_list", "maquinaria_edos_list",
                          "maquinaria_tipos_list", "maquinaria_registro_ops_list"):
                cache.delete(clave)
            messages.success(request, f"Máquina {payload['codigo']} registrada exitosamente.")
            return redirect("maquinaria:index")

        messages.warning(request, f"El API rechazó el registro. {_detalle_error_api(response)}")
        return render(request, self.template_name, {"form": form})

class EliminarMaquina(generic.View):
    """Llama a la API para deshabilitar o eliminar una máquina por su código."""

    def post(self, request, codigo):
        url = f"{API_URL}/v1/maquina/{codigo}/deshabilitar/"
        try:
            # Usamos PATCH según la definición de DeshabilitarMaquinaAPIView
            res = SESSION.patch(url, timeout=5)
            if res.status_code == 200:
                messages.success(request, f"Máquina {codigo} dada de baja correctamente.")
            else:
                messages.error(request, "No se pudo procesar la baja de la máquina.")
        except requests.exceptions.RequestException:
            messages.error(request, "Error de conexión con el servidor de API.")

        return redirect("maquinaria:index")

class ReactivarMaquina(generic.View):
    """Llama a la API para reactivar una máquina que estaba deshabilitada (DESHA -> OPERA)."""

    def post(self, request, codigo):
        url = f"{API_URL}/v1/maquina/{codigo}/reactivar/"
        try:
            res = SESSION.patch(url, timeout=5)
            if res.status_code == 200:
                messages.success(request, f"Máquina {codigo} reincorporada a estado OPERATIVA.")
            else:
                messages.error(request, "No se pudo reactivar la máquina.")
        except requests.exceptions.RequestException:
            messages.error(request, "Error de conexión con el servidor de API.")

        return redirect("maquinaria:detail", codigo=codigo)

class WikiMaquinasView(TemplateView):
    template_name = "maquinaria/wiki_maquinas.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['seccion'] = 'maquinaria'
        context['subseccion'] = 'wiki'
        return context

    

class RegistroOpsView(generic.View):
    """Página de registro de horas de operación (editar/eliminar)."""

    template_name = "maquinaria/registro_ops.html"

    def get(self, request):
        usuario = request.session.get("usuario")
        if not usuario:
            messages.warning(request, "Inicia sesión para continuar.")
            return redirect("usuarios:index")

        maquinas = cache.get("maquinaria_registro_ops_list")
        if maquinas is None:
            try:
                res = SESSION.get(f"{API_URL}/v1/maquina/list/", timeout=5)
                maquinas = res.json() if res.status_code == 200 else []
                cache.set("maquinaria_registro_ops_list", maquinas, 300)
            except requests.exceptions.RequestException:
                maquinas = []

        context = {
            "seccion": "maquinaria",
            "subseccion": "registro-ops",
            "maquinas": maquinas,
            "usuario": usuario,
            "base_template": "base_tecni.html" if usuario.get("rol") == "TECNI" else "base_admin.html",
        }
        return render(request, self.template_name, context)
