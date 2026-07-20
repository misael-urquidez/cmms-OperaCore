import requests
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render
from django.views import generic

API_URL = f"{settings.API_BASE_URL}/inventario"

# Sesion HTTP a nivel de modulo: reusa la conexion TCP con el api/.
SESSION = requests.Session()

# El ping es solo un status, no data real: cache de 30 seg para no
# pegarle al api/ en cada click al modulo.
PING_TTL = 30


class Index(generic.View):
    """Pantalla principal del modulo Inventario. Consume el api/ por HTTP."""

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


# A partir de aqui sigue el patron de tu maestro (home/views.py):
# cada vista pega a un endpoint del api/ con requests.get/post/put/delete
# y le pasa la respuesta (.json()) al template via el contexto. Ejemplo:
#
# class ListarAlgo(generic.View):
#     template_name = "inventario/list.html"
#
#     def get(self, request):
#         data = requests.get(f"{API_URL}/v1/list/").json()
#         return render(request, self.template_name, {"items": data})
#
# class CrearAlgo(generic.View):
#     template_name = "inventario/create.html"
#
#     def get(self, request):
#         return render(request, self.template_name, {})
#
#     def post(self, request):
#         payload = {"campo": request.POST.get("campo")}
#         requests.post(f"{API_URL}/v2/create/", json=payload)
#         return redirect("inventario:index")
