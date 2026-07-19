from django.shortcuts import render, redirect
from django.views import generic
from django.contrib import messages
import requests

from django.conf import settings


API_URL = f"{settings.API_BASE_URL}/fallas"


class ReporteFalla(generic.View):
    template_name = "fallas/reporte_falla.html"
    context = {}
    url_severidades = f"{API_URL}/v1/tipos-severidad/"
    url_tipos_falla = f"{API_URL}/v1/tipos-falla/"
    url_maquinas = f"{API_URL}/v1/maquinas/"
    url_estados = f"{API_URL}/v1/estados-reporte/"
    url_create = f"{API_URL}/v2/reportes/create/"
    response = None
    payload = {}

    def get(self, request):
        severidades = requests.get(url=self.url_severidades).json()
        tipos_falla = requests.get(url=self.url_tipos_falla).json()
        maquinas = requests.get(url=self.url_maquinas).json()
        estados = requests.get(url=self.url_estados).json()
        self.context = {
            "severidades": severidades,
            "tipos_falla": tipos_falla,
            "maquinas": maquinas,
            "estados": estados,
        }
        return render(request, self.template_name, self.context)

    def post(self, request):
        self.payload = {
            "asunto": request.POST.get("asunto"),
            "descripcion": request.POST.get("descripcion"),
            "causaRaiz": request.POST.get("causaRaiz"),
            "tiempoParo": request.POST.get("tiempoParo"),
            "maquina": request.POST.get("maquina"),
            "tipo_falla": request.POST.get("tipo_falla"),
            "tipo_severidad": request.POST.get("tipo_severidad"),
                        "estado_reporte": request.POST.get("estado_reporte")

        }


        archivo = request.FILES.get("imagen")
        files = {"imagen": archivo} if archivo else None
        self.response = requests.post(url=self.url_create, data=self.payload, files=files)
        if self.response.status_code == 201:
            messages.success(request, "El reporte de falla ha sido registrado")
            return redirect("fallas:lista")
        else:
            messages.warning(request, "Error al registrar el reporte")



class ListaReportes(generic.View):
    template_name = "fallas/lista_reportes.html"
    context = {}
    url_base = f"{API_URL}/v1/reportes/list/"
    response = None

    def get(self, request):
        self.response = requests.get(url=self.url_base).json()
        self.context = {"reportes": self.response}
        return render(request, self.template_name, self.context)
