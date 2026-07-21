import requests
from django.conf import settings
from django.shortcuts import render
from django.views import generic

API_URL = f"{settings.API_BASE_URL}/maquinaria"


import requests
from django.conf import settings
from django.shortcuts import render
from django.views import generic

API_URL = f"{settings.API_BASE_URL}/maquinaria"


class Index(generic.View):
    """Dashboard principal: Muestra métricas generales y el listado de estado de la maquinaria."""

    template_name = "maquinaria/index.html"

    def get(self, request):
        try:
            res = requests.get(f"{API_URL}/api/v1/list/", timeout=5)
            maquinas = res.json() if res.status_code == 200 else []
        except requests.exceptions.RequestException:
            maquinas = []

        # Cálculo de contadores para las tarjetas del Dashboard
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
        print(f"--> Consultando URL de la API: {url}") # Imprime en tu terminal de Django
        try:
            res = requests.get(url, timeout=5)
            print(f"--> Código de estado API: {res.status_code}")
            print(f"--> Respuesta API: {res.text}")
            
            if res.status_code == 200:
                data = res.json()
            else:
                data = None
        except requests.exceptions.RequestException as e:
            print(f"--> Error de conexión con la API: {e}")
            data = None

        return render(request, self.template_name, {"maquina": data})

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
