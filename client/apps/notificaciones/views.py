import requests
from django.conf import settings
from django.http import JsonResponse
from django.views import View

API_URL = f"{settings.API_BASE_URL}/notificaciones"
SESSION = requests.Session()


class NotificacionesListAPIView(View):
    def get(self, request):
        usuario = request.session.get("usuario")
        params = {}
        if usuario:
            params["trabajador"] = usuario.get("numeroNomina", "")
            params["rol"] = usuario.get("rol", "")
        try:
            r = SESSION.get(f"{API_URL}/v1/notificaciones/list/", params=params, timeout=5)
            cuerpo = r.json()
        except (requests.RequestException, ValueError):
            return JsonResponse([], safe=False, status=502)
        return JsonResponse(cuerpo, safe=False, status=r.status_code)
