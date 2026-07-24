import requests
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render, redirect, get_object_or_404
from django.views import generic
from .forms import MaquinaForm
from django.views.generic import TemplateView

API_URL = f"{settings.API_BASE_URL}/maquinaria"

# Sesion HTTP a nivel de modulo: reusa la conexion TCP con la API
SESSION = requests.Session()

# Cache de 30 segundos para la verificacion de estado (ping)
PING_TTL = 30


class Index(generic.View):
    """Dashboard principal: Muestra métricas generales y el estado del servicio."""

    template_name = "maquinaria/index.html"

    def get(self, request):
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

        total_maquinas = len(maquinas)
        operativas = sum(
            1 for m in maquinas 
            if str(m.get("estado_maquina", "")).lower() in ["activo", "operativa", "en linea"]
        )
        en_mantenimiento = total_maquinas - operativas

        context = {
            "modulo": "Maquinaria",
            "api_status": api_status,
            "maquinas": maquinas,
            "total_maquinas": total_maquinas,
            "operativas": operativas,
            "en_mantenimiento": en_mantenimiento,
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

        return render(request, self.template_name, {"maquina": data})


class CrearMaquina(generic.View):
    template_name = "maquinaria/crear_maquina.html"

    def get(self, request):
        form = MaquinaForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = MaquinaForm(request.POST, request.FILES)
        
        if form.is_valid():
            payload = form.cleaned_data.copy()
            files_payload = {}

            # Autogenerar el código correlativo
            try:
                res = SESSION.get(f"{API_URL}/v1/maquina/list/", timeout=5)
                maquinas_existentes = res.json() if res.status_code == 200 else []
                siguiente_num = len(maquinas_existentes) + 1
                payload["codigo"] = f"MAQ{siguiente_num:03d}"
            except requests.exceptions.RequestException:
                payload["codigo"] = "MAQ999"

            # Formatear la fecha a ISO string si existe
            if "fechaInstalacion" in payload and payload["fechaInstalacion"]:
                payload["fechaInstalacion"] = payload["fechaInstalacion"].isoformat()

            # Extraer archivos del formulario para multipart/form-data
            if "imagen_url" in payload and payload["imagen_url"]:
                imagen_file = payload.pop("imagen_url")
                files_payload["imagen_url"] = (imagen_file.name, imagen_file.read(), imagen_file.content_type)

            if "modelo_3d" in payload and payload["modelo_3d"]:
                modelo_file = payload.pop("modelo_3d")
                files_payload["modelo_3d"] = (modelo_file.name, modelo_file.read(), modelo_file.content_type)

            try:
                response = SESSION.post(
                    f"{API_URL}/v1/maquina/create/", 
                    data=payload, 
                    files=files_payload if files_payload else None, 
                    timeout=10
                )
                if response.status_code in [200, 201]:
                    return redirect("maquinaria:index")
            except requests.exceptions.RequestException:
                pass

        return render(request, self.template_name, {"form": form})

class WikiMaquinasView(TemplateView):
    template_name = "maquinaria/wiki_maquinas.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['seccion'] = 'maquinaria'
        context['subseccion'] = 'wiki'
        return context