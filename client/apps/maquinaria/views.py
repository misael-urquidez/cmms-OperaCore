import requests
from django.conf import settings
<<<<<<< HEAD
from django.shortcuts import render, redirect, get_object_or_404
=======
from django.core.cache import cache
from django.shortcuts import render
>>>>>>> 35c7fe2ef22a405e758ee1f3f550909d9ca8b569
from django.views import generic
from .forms import MaquinaForm

API_URL = f"{settings.API_BASE_URL}/maquinaria"

<<<<<<< HEAD
=======
# Sesion HTTP a nivel de modulo: reusa la conexion TCP con el api/.
SESSION = requests.Session()

# El ping es solo un status, no data real: cache de 30 seg para no
# pegarle al api/ en cada click al modulo.
PING_TTL = 30


>>>>>>> 35c7fe2ef22a405e758ee1f3f550909d9ca8b569
class Index(generic.View):
    """Dashboard principal: Muestra métricas generales y el listado de estado de la maquinaria."""

    template_name = "maquinaria/index.html"

    def get(self, request):
<<<<<<< HEAD
        try:
            res = requests.get(f"{API_URL}/api/v1/list/", timeout=5)
            maquinas = res.json() if res.status_code == 200 else []
        except requests.exceptions.RequestException:
            maquinas = []
=======
        response = cache.get("maquinaria_ping")
        if response is None:
            try:
                response = SESSION.get(f"{API_URL}/ping/", timeout=5).json()
            except requests.exceptions.RequestException:
                response = {"status": "sin conexion con el api"}
            cache.set("maquinaria_ping", response, PING_TTL)
        return render(request, self.template_name, {"modulo": "Maquinaria", "api_status": response})
>>>>>>> 35c7fe2ef22a405e758ee1f3f550909d9ca8b569

        total_maquinas = len(maquinas)
        operativas = sum(
            1 for m in maquinas 
            if m.get("estado_maquina", "").lower() in ["activo", "operativa", "en linea"]
        )
        en_mantenimiento = total_maquinas - operativas

        context = {
            "modulo": "Maquinaria",
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
            res = requests.get(f"{API_URL}/api/v1/list/", timeout=5)
            data = res.json() if res.status_code == 200 else []
        except requests.exceptions.RequestException:
            data = []

        return render(request, self.template_name, {"maquinas": data})


class DetalleMaquina(generic.View):
    """Detalle técnico e individual de una máquina con su visor 3D."""

    template_name = "maquinaria/detalle_maquina.html"

    def get(self, request, codigo):
        url = f"{API_URL}/api/v1/{codigo}/"
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
            else:
                data = None
        except requests.exceptions.RequestException:
            data = None

        return render(request, self.template_name, {"maquina": data})


class CrearMaquina(generic.View):
    template_name = "maquinaria/crear_maquina.html"

    def get(self, request):
        form = MaquinaForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        # IMPORTANTE: Se debe incluir request.FILES para capturar las imágenes y modelos 3D
        form = MaquinaForm(request.POST, request.FILES)
        
        if form.is_valid():
            payload = form.cleaned_data
            files_payload = {}

            # Autogenerar el código correlativo
            try:
                res = requests.get(f"{API_URL}/api/v1/list/", timeout=5)
                maquinas_existentes = res.json() if res.status_code == 200 else []
                siguiente_num = len(maquinas_existentes) + 1
                payload["codigo"] = f"MAQ{siguiente_num:03d}"
            except requests.exceptions.RequestException:
                payload["codigo"] = "MAQ999"

            # Formatear la fecha a string ISO
            if "fechaInstalacion" in payload and payload["fechaInstalacion"]:
                payload["fechaInstalacion"] = payload["fechaInstalacion"].isoformat()

            # Extraer los archivos subidos del formulario si existen para enviarlos por multipart/form-data
            if "imagen_url" in payload and payload["imagen_url"]:
                imagen_file = payload.pop("imagen_url")
                files_payload["imagen_url"] = (imagen_file.name, imagen_file.read(), imagen_file.content_type)

            if "modelo_3d" in payload and payload["modelo_3d"]:
                modelo_file = payload.pop("modelo_3d")
                files_payload["modelo_3d"] = (modelo_file.name, modelo_file.read(), modelo_file.content_type)

            try:
                # Si tu API acepta archivos mediante multipart, usamos 'data' y 'files'
                response = requests.post(
                    f"{API_URL}/api/v1/create/", 
                    data=payload, 
                    files=files_payload if files_payload else None, 
                    timeout=10
                )
                if response.status_code in [200, 201]:
                    return redirect("maquinaria:index")
            except requests.exceptions.RequestException:
                pass

        return render(request, self.template_name, {"form": form})

# A partir de aqui sigue el patron de tu maestro (home/views.py):
# cada vista pega a un endpoint del api/ con requests.get/post/put/delete
# y le pasa la respuesta (.json()) al template via el contexto. Ejemplo:
#
# class ListarAlgo(generic.View):
#     template_name = "maquinaria/list.html"
#
#     def get(self, request):
#         data = requests.get(f"{API_URL}/v1/list/").json()
#         return render(request, self.template_name, {"items": data})
#
# class CrearAlgo(generic.View):
#     template_name = "maquinaria/create.html"
#
#     def get(self, request):
#         return render(request, self.template_name, {})
#
#     def post(self, request):
#         payload = {"campo": request.POST.get("campo")}
#         requests.post(f"{API_URL}/v2/create/", json=payload)
#         return redirect("maquinaria:index")
