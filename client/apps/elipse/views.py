import json

import requests
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import generic

API_URL = f"{settings.API_BASE_URL}/elipse"

# Sesion HTTP a nivel de modulo: reusa la conexion TCP con el api/.
# Aqui no se cachea nada: es un chat, cada pregunta es distinta.
SESSION = requests.Session()

# Las sugerencias si se cachean: son una constante del api que casi nunca
# cambia, y las pide cada carga de la pantalla.
SUGERENCIAS_TTL = 60 * 60  # 1 hora


class Index(generic.View):
    """Pantalla de chat de Elipse. Solo para sesion iniciada (mismo
    candado que admin_dashboard)."""

    template_name = "elipse/index.html"

    def get(self, request):
        usuario = request.session.get("usuario")
        if not usuario:
            messages.warning(request, "Inicia sesión para continuar.")
            return redirect("usuarios:index")
        return render(request, self.template_name, {"seccion": "elipse", "usuario": usuario})


class Chat(generic.View):
    """Recibe la pregunta del navegador y la reenvia al api/, igual que
    el resto de vistas del client (patron requests.post -> api/)."""

    def post(self, request):
        usuario = request.session.get("usuario")
        if not usuario:
            return JsonResponse({"error": "Sesión expirada, vuelve a iniciar sesión."}, status=401)

        try:
            body = json.loads(request.body)
        except ValueError:
            return JsonResponse({"error": "Petición inválida."}, status=400)

        try:
            resp = SESSION.post(f"{API_URL}/chat/", json=body, timeout=25)
            return JsonResponse(resp.json(), status=resp.status_code)
        except requests.exceptions.RequestException:
            return JsonResponse({"error": "No se pudo conectar con el servidor de Elipse."}, status=502)


class AutocompletarFalla(generic.View):
    """Reenvia al api/ la descripcion libre de una falla para que Elipse
    proponga los campos del formulario de reporte de falla. Mismo patron
    que Chat: solo reenvia, no toca la BD."""

    def post(self, request):
        usuario = request.session.get("usuario")
        if not usuario:
            return JsonResponse({"error": "Sesión expirada, vuelve a iniciar sesión."}, status=401)

        try:
            body = json.loads(request.body)
        except ValueError:
            return JsonResponse({"error": "Petición inválida."}, status=400)

        try:
            resp = SESSION.post(f"{API_URL}/autocompletar-falla/", json=body, timeout=25)
            return JsonResponse(resp.json(), status=resp.status_code)
        except requests.exceptions.RequestException:
            return JsonResponse({"error": "No se pudo conectar con el servidor de Elipse."}, status=502)


class Sugerencias(generic.View):
    """Preguntas rapidas que se muestran como chips en la bienvenida.

    Las define el api (PREGUNTAS_RAPIDAS) para no tener la misma lista
    duplicada en Python y en JS."""

    def get(self, request):
        if not request.session.get("usuario"):
            return JsonResponse({"sugerencias": []}, status=401)

        data = cache.get("elipse_sugerencias")
        if data is None:
            try:
                resp = SESSION.get(f"{API_URL}/sugerencias/", timeout=5)
                data = resp.json()
                cache.set("elipse_sugerencias", data, SUGERENCIAS_TTL)
            except (requests.exceptions.RequestException, ValueError):
                # Sin chips la pantalla sigue siendo usable: se escribe y ya.
                return JsonResponse({"sugerencias": []})
        return JsonResponse(data)
