import json

import requests
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

API_URL = f"{settings.API_BASE_URL}/monitoreo"
SESSION = requests.Session()


def consultar_maquinas():
    try:
        respuesta = SESSION.get(f"{API_URL}/maquinas/", timeout=5)
        respuesta.raise_for_status()
        return respuesta.json(), None
    except requests.RequestException:
        return [], "No fue posible conectar con el API de monitoreo."


class Index(View):
    template_name = "monitoreo/index.html"

    def get(self, request):
        maquinas, error = consultar_maquinas()
        return render(request, self.template_name, {
            "maquinas": maquinas, "error": error, "seccion": "monitoreo",
        })


class DatosMaquinasAPIView(View):
    def get(self, request):
        maquinas, error = consultar_maquinas()
        return JsonResponse({"maquinas": maquinas, "error": error})


class IndicadoresMaquinaAPIView(View):
    def get(self, request, codigo):
        try:
            respuesta = SESSION.get(f"{API_URL}/maquinas/{codigo}/indicadores/", timeout=5)
            respuesta.raise_for_status()
        except requests.RequestException:
            return JsonResponse({"detail": "No fue posible conectar con el API."}, status=502)
        return JsonResponse(respuesta.json())


class HistorialMaquinaAPIView(View):
    def get(self, request, codigo):
        limite = request.GET.get("limite", "20")
        try:
            respuesta = SESSION.get(
                f"{API_URL}/maquinas/{codigo}/historial/", params={"limite": limite}, timeout=5,
            )
            respuesta.raise_for_status()
        except requests.RequestException:
            return JsonResponse({"detail": "No fue posible conectar con el API."}, status=502)
        return JsonResponse(respuesta.json())


class EstadoMaquinaAPIView(View):
    def get(self, request, codigo):
        try:
            respuesta = SESSION.get(f"{API_URL}/maquinas/{codigo}/estado/", timeout=5)
            respuesta.raise_for_status()
        except requests.RequestException:
            return JsonResponse({"detail": "No fue posible conectar con el API."}, status=502)
        return JsonResponse(respuesta.json())


class CatalogosMaquinaAPIView(View):
    def get(self, request):
        try:
            respuesta = SESSION.get(f"{API_URL}/catalogos/", timeout=5)
            respuesta.raise_for_status()
        except requests.RequestException:
            return JsonResponse({"detail": "No fue posible conectar con el API."}, status=502)
        return JsonResponse(respuesta.json())


class CrearMaquinaAPIView(View):
    def post(self, request):
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except ValueError:
            return JsonResponse({"detail": "JSON inválido."}, status=400)
        try:
            respuesta = SESSION.post(f"{API_URL}/maquinas/crear/", json=payload, timeout=5)
        except requests.RequestException:
            return JsonResponse({"detail": "No fue posible conectar con el API."}, status=502)
        try:
            cuerpo = respuesta.json()
        except ValueError:
            cuerpo = {"detail": "Respuesta inválida del API."}
        return JsonResponse(cuerpo, status=respuesta.status_code, safe=False)


class ModoMonitoreoAPIView(View):
    def patch(self, request, codigo):
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except ValueError:
            return JsonResponse({"detail": "JSON inválido."}, status=400)
        try:
            respuesta = SESSION.patch(f"{API_URL}/maquinas/{codigo}/modo/", json=payload, timeout=5)
        except requests.RequestException:
            return JsonResponse({"detail": "No fue posible conectar con el API."}, status=502)
        try:
            cuerpo = respuesta.json()
        except ValueError:
            cuerpo = {"detail": "Respuesta inválida del API."}
        return JsonResponse(cuerpo, status=respuesta.status_code, safe=False)


class LecturaManualAPIView(View):
    def post(self, request):
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except ValueError:
            return JsonResponse({"detail": "JSON inválido."}, status=400)
        payload["origen"] = "manual"
        try:
            respuesta = SESSION.post(f"{API_URL}/lecturas/", json=payload, timeout=5)
        except requests.RequestException:
            return JsonResponse({"detail": "No fue posible conectar con el API."}, status=502)
        try:
            cuerpo = respuesta.json()
        except ValueError:
            cuerpo = {"detail": "Respuesta inválida del API."}
        return JsonResponse(cuerpo, status=respuesta.status_code, safe=False)


class SimularLecturaAPIView(View):
    def post(self, request, codigo):
        try:
            respuesta = SESSION.post(f"{API_URL}/maquinas/{codigo}/simular/", timeout=5)
        except requests.RequestException:
            return JsonResponse({"detail": "No fue posible conectar con el API."}, status=502)
        try:
            cuerpo = respuesta.json()
        except ValueError:
            cuerpo = {"detail": "Respuesta inválida del API."}
        return JsonResponse(cuerpo, status=respuesta.status_code, safe=False)


class RegistroOpsAPIView(View):
    def post(self, request, codigo):
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except ValueError:
            return JsonResponse({"detail": "JSON inválido."}, status=400)
        try:
            respuesta = SESSION.post(f"{API_URL}/maquinas/{codigo}/registro-ops/", json=payload, timeout=5)
        except requests.RequestException:
            return JsonResponse({"detail": "No fue posible conectar con el API."}, status=502)
        try:
            cuerpo = respuesta.json()
        except ValueError:
            cuerpo = {"detail": "Respuesta inválida del API."}
        return JsonResponse(cuerpo, status=respuesta.status_code, safe=False)
