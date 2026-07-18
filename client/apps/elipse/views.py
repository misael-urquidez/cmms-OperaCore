import json

import requests
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import generic

API_URL = f"{settings.API_BASE_URL}/elipse"


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
            resp = requests.post(f"{API_URL}/chat/", json=body, timeout=25)
            return JsonResponse(resp.json(), status=resp.status_code)
        except requests.exceptions.RequestException:
            return JsonResponse({"error": "No se pudo conectar con el servidor de Elipse."}, status=502)
