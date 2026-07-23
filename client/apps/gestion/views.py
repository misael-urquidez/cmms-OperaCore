import requests
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.http import Http404
from django.shortcuts import redirect, render
from django.views import generic

from .registry import get_modulos, get_tabla

SESSION = requests.Session()
LIST_TTL = 15          # segundos de cache para listados
FK_CHOICES_TTL = 60 * 5  # 5 min para catalogos usados en selects


def _api_base(api_app):
    return f"{settings.API_BASE_URL}/{api_app}"


def _fetch_list(config):
    """GET al endpoint de listado de una tabla, con cache corta."""
    cache_key = f"gestion_list_{config['slug']}"
    data = cache.get(cache_key)
    if data is not None:
        return data, True

    url = f"{_api_base(config['api_app'])}/{config['list_path']}"
    try:
        res = SESSION.get(url, timeout=5)
        if res.status_code != 200:
            return [], False
        data = res.json()
        cache.set(cache_key, data, LIST_TTL)
        return data, True
    except (requests.exceptions.RequestException, ValueError):
        return [], False


def _fetch_fk_choices(fk_slug):
    """Trae las opciones para un <select> que referencia otra tabla del registro."""
    fk_config = get_tabla(fk_slug)
    if not fk_config:
        return []
    data, ok = _fetch_list(fk_config)
    if not ok:
        return []
    return data


def _resolver_choices(config):
    """Para cada campo tipo 'select' con fk, agrega sus opciones (value/label).
    Si el campo tiene 'fk_parent', incluye 'parent' en cada opcion para
    permitir cascading en el template.
    Si el campo tiene 'opciones' inline, las usa directamente."""
    campos = []
    for campo in config["campos"]:
        campo = dict(campo)
        if campo.get("tipo") == "select" and campo.get("fk"):
            crudos = _fetch_fk_choices(campo["fk"])
            parent_key = campo.get("fk_parent_key")
            campo["opciones"] = [
                {
                    "value": item.get(campo["fk_value"]),
                    "label": item.get(campo["fk_label"]),
                    "parent": item.get(parent_key) if parent_key else None,
                }
                for item in crudos
            ]
        campos.append(campo)
    return campos


def _get_config_or_404(slug):
    config = get_tabla(slug)
    if not config:
        raise Http404(f"'{slug}' no esta registrado en Gestion.")
    return config


def _pk_dict(config, pk):
    """Reconstruye el dict que necesita detail_path.format(**...).
    Si pk_field es simple (string), regresa {"pk": pk} (caso de siempre).
    Si pk_field es lista (llave compuesta), separa pk por '~' y arma
    {nombre_columna: valor} para cada componente, en el mismo orden."""
    campo_pk = config["pk_field"]
    if isinstance(campo_pk, (list, tuple)):
        return dict(zip(campo_pk, pk.split("~")))
    return {"pk": pk}


def _fetch_detail(config, pk):
    """GET a un registro puntual, usado para precargar el form de edicion."""
    detail_path = config.get("detail_path")
    if not detail_path:
        return None, False
    url = f"{_api_base(config['api_app'])}/{detail_path.format(**_pk_dict(config, pk))}"
    try:
        res = SESSION.get(url, timeout=5)
        if res.status_code != 200:
            return None, False
        return res.json(), True
    except (requests.exceptions.RequestException, ValueError):
        return None, False


def _resolver_choices_con_valores(config, valores=None):
    """Igual que _resolver_choices pero, si hay 'valores' (edicion), marca
    la opcion seleccionada y precarga el valor de cada campo.
    Tambien soporta opciones inline en el registry."""
    valores = valores or {}
    campos = []
    for campo in config["campos"]:
        campo = dict(campo)
        campo["valor"] = "" if campo.get("tipo") == "password" else valores.get(campo["name"], "")
        if campo.get("tipo") == "select" and campo.get("fk"):
            crudos = _fetch_fk_choices(campo["fk"])
            parent_key = campo.get("fk_parent_key")
            campo["opciones"] = [
                {
                    "value": item.get(campo["fk_value"]),
                    "label": item.get(campo["fk_label"]),
                    "parent": item.get(parent_key) if parent_key else None,
                }
                for item in crudos
            ]
        campos.append(campo)
    return campos


def _build_payload(config, post_data, es_edicion=False, archivos=None):
    payload = {}
    errores = []
    file_names = {c["name"] for c in config["campos"] if c.get("tipo") == "file"}
    for campo in config["campos"]:
        if campo.get("tipo") == "file":
            continue
        valor = post_data.get(campo["name"], "").strip()
        requerido = campo.get("requerido") and not (es_edicion and campo.get("tipo") == "password")
        if requerido and not valor:
            errores.append(f"El campo '{campo['label']}' es obligatorio.")
        if valor:
            payload[campo["name"]] = valor
    return payload, errores


def _extraer_archivos(config, archivos):
    """Extrae de request.FILES los campos declarados como tipo 'file'.
    Usa 'file_api_name' como key si existe, si no usa el name del campo."""
    files = {}
    for campo in config["campos"]:
        if campo.get("tipo") == "file" and campo["name"] in archivos:
            api_name = campo.get("file_api_name") or campo["name"]
            files[api_name] = archivos[campo["name"]]
    return files or None


def _invalidar_cache(config):
    cache.delete(f"gestion_list_{config['slug']}")
    cache.delete_many(config.get("invalidate_cache_keys", []))


# ---------------------------------------------------------------------------
class GestionIndex(generic.View):
    template_name = "gestion/index.html"

    def get(self, request):
        context = {
            "modulos": get_modulos(),
            "seccion": "gestion",
        }
        return render(request, self.template_name, context)


class GestionListView(generic.View):
    template_name = "gestion/list_generic.html"

    def get(self, request, slug):
        config = _get_config_or_404(slug)
        registros, ok = _fetch_list(config)
        if not ok:
            messages.warning(request, "No se pudo conectar con la API.")

        columnas = [c for c in config["campos"] if c.get("columna", True)]

        context = {
            "config": config,
            "registros": registros,
            "columnas": columnas,
            "seccion": "gestion",
            "subseccion": slug,
        }
        return render(request, self.template_name, context)


class GestionCreateView(generic.View):
    template_name = "gestion/form_generic.html"

    def get(self, request, slug):
        config = _get_config_or_404(slug)
        campos = _resolver_choices(config)
        context = {
            "config": config,
            "campos": campos,
            "seccion": "gestion",
            "subseccion": slug,
        }
        return render(request, self.template_name, context)

    def post(self, request, slug):
        config = _get_config_or_404(slug)

        payload, errores = _build_payload(config, request.POST)
        if errores:
            for e in errores:
                messages.warning(request, e)
            return redirect("gestion:crear", slug=slug)

        url = f"{_api_base(config['api_app'])}/{config['create_path']}"
        try:
            files = _extraer_archivos(config, request.FILES)
            res = SESSION.post(url, data=payload, files=files, timeout=10)
            if res.status_code in (200, 201):
                _invalidar_cache(config)
                messages.success(request, f"{config['label']} registrado exitosamente.")
                return redirect("gestion:list", slug=slug)
            else:
                detalle = ""
                try:
                    detalle = " ".join(f"{k}: {v}" for k, v in res.json().items())
                except ValueError:
                    pass
                messages.warning(request, f"El API rechazó el registro. {detalle}".strip())
        except requests.exceptions.RequestException:
            messages.warning(request, "No se pudo conectar con el servidor.")

        return redirect("gestion:crear", slug=slug)


class GestionEditView(generic.View):
    """Edita un registro existente. Solo disponible si la tabla trae
    'detail_path' en el registro (ver registry.py)."""

    template_name = "gestion/form_generic.html"

    def _url_update(self, config, pk):
        path = config.get("update_path") or config.get("detail_path")
        return f"{_api_base(config['api_app'])}/{path.format(**_pk_dict(config, pk))}"

    def get(self, request, slug, pk):
        config = _get_config_or_404(slug)
        if not config.get("detail_path"):
            raise Http404(f"'{slug}' no tiene edicion habilitada.")

        valores, ok = _fetch_detail(config, pk)
        if not ok:
            messages.warning(request, "No se pudo cargar el registro.")
            return redirect("gestion:list", slug=slug)

        campos = _resolver_choices_con_valores(config, valores)
        context = {
            "config": config,
            "campos": campos,
            "modo": "editar",
            "pk": pk,
            "seccion": "gestion",
            "subseccion": slug,
        }
        return render(request, self.template_name, context)

    def post(self, request, slug, pk):
        config = _get_config_or_404(slug)
        if not config.get("detail_path"):
            raise Http404(f"'{slug}' no tiene edicion habilitada.")

        payload, errores = _build_payload(config, request.POST, es_edicion=True)
        if errores:
            for e in errores:
                messages.warning(request, e)
            return redirect("gestion:editar", slug=slug, pk=pk)

        metodo = config.get("update_method", "PATCH")
        url = self._url_update(config, pk)
        try:
            files = _extraer_archivos(config, request.FILES)
            res = SESSION.request(metodo, url, data=payload, files=files, timeout=10)
            if res.status_code in (200, 201):
                _invalidar_cache(config)
                messages.success(request, f"{config['label']} actualizado exitosamente.")
                return redirect("gestion:list", slug=slug)
            else:
                detalle = ""
                try:
                    detalle = " ".join(f"{k}: {v}" for k, v in res.json().items())
                except ValueError:
                    pass
                messages.warning(request, f"El API rechazó la edición. {detalle}".strip())
        except requests.exceptions.RequestException:
            messages.warning(request, "No se pudo conectar con el servidor.")

        return redirect("gestion:editar", slug=slug, pk=pk)


class GestionDeleteView(generic.View):
    """Borra un registro. Solo disponible si la tabla trae 'delete_path'.
    Se dispara con POST (no GET) para no borrar nada por accidente ni por
    un crawler siguiendo el link."""

    def post(self, request, slug, pk):
        config = _get_config_or_404(slug)
        delete_path = config.get("delete_path")
        if not delete_path:
            raise Http404(f"'{slug}' no tiene borrado habilitado.")

        metodo = config.get("delete_method", "DELETE")
        url = f"{_api_base(config['api_app'])}/{delete_path.format(**_pk_dict(config, pk))}"
        try:
            res = SESSION.request(metodo, url, timeout=10)
            if res.status_code in (200, 202, 204):
                _invalidar_cache(config)
                messages.success(request, f"{config['label']} eliminado.")
            else:
                messages.warning(request, "El API rechazó el borrado (¿el registro está en uso por otra tabla?).")
        except requests.exceptions.RequestException:
            messages.warning(request, "No se pudo conectar con el servidor.")

        return redirect("gestion:list", slug=slug)
