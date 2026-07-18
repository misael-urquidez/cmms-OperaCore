import requests
from urllib import response
from django.conf import settings
from django.shortcuts import render, redirect
from django.views import generic
import requests 
from . import forms

API_URL = f"{settings.API_BASE_URL}/fallas"


class Index(generic.View):
    """Pantalla principal del modulo Fallas. Consume el api/ por HTTP."""

    template_name = "fallas/index.html"

    def get(self, request):
        try:
            response = requests.get(f"{API_URL}/ping/", timeout=5).json()
        except requests.exceptions.RequestException:
            response = {"status": "sin conexion con el api"}
        return render(request, self.template_name, {"modulo": "Fallas", "api_status": response})

#---------------------------------------------------------------------------
#------------TIPO FALLA ----------------------------------------------------
#---------------------------------------------------------------------------
class ListTipoFalla(generic.View):
    template_name = "fallas/list_tipo_falla.html"
    context = {}
    url_base = f"http://localhost:8000/api/{API_URL}/v1/tipo_falla/list/"
    response = None

    def get(self, request):
        self.response = requests.get(self.url_base).json()
        self.context = {
            "tipos_falla": self.response
        }
        return render(request, self.template_name, self.context)
    
class DetailTipoFalla(generic.View):
    template_name = "fallas/detail_tipo_falla.html"
    context = {}
    url_base = f"http://localhost:8000/api/{API_URL}/v1/tipo_falla/"
    response = None

    def get(self, request, pk):
        self.url_base += f"{pk}/"
        self.response = requests.get(self.url_base).json()
        self.context = {
            "tipo_falla": self.response
        }
        return render(request, self.template_name, self.context)
    
class CreateTipoFalla(generic.View):
    template_name = "fallas/create_tipo_falla.html"
    context = {}
    url_base = f"http://localhost:8000/api/{API_URL}/v1/tipo_falla/create/"
    response = None
    payload = {}
    form_class = forms.CrearTipoFalla

    def get(self, request):
        self.context = {
            "form": self.form_class()
        }
        return render(request, self.template_name, self.context)

    def post(self, request):
        nombre = request.POST["nombre"]
        descripcion = request.POST["descripcion"]
        self.payload = {
            "nombre": nombre,
            "descripcion": descripcion
        }

        response = requests.post(self.url_base, data=self.payload)

        return redirect("fallas:list_tipos_falla")
    
class UpdateTipoFalla(generic.View):
    template_name = "fallas/update_tipo_falla.html"
    context = {}
    url_get = f"http://localhost:8000/api/{API_URL}/v1/tipo_falla/"
    url_put = f"http://localhost:8000/api/{API_URL}/v1/tipo_falla/update/"
    response = None
    payload = {}

    def get(self, request, pk):
        self.url_get += f"{pk}/"
        self.response = requests.get(self.url_get).json()
        self.context = {
            "tipo_falla": self.response
        }
        return render(request, self.template_name, self.context)

    def post(self, request, pk):
        self.url_put += f"{pk}/"
        self.payload = {
            "nombre": request.POST.get("nombre"),
            "descripcion": request.POST.get("descripcion")
        }

        self.response = requests.put(url=self.url_put, data=self.payload).json()
        self.context = {
            "tipo_falla": self.response
        }
        return redirect("fallas:list_tipos_falla")

#---------------------------------------------------------------------------
#------------TIPO SEVERIDAD ------------------------------------------------
#---------------------------------------------------------------------------
class ListTipoSeveridad(generic.View):
    template_name = "fallas/list_tipo_severidad.html"
    context = {}
    url_base = f"http://localhost:8000/api/{API_URL}/v1/tipo_severidad/list/"
    response = None

    def get(self, request):
        self.response = requests.get(self.url_base).json()
        self.context = {
            "tipos_severidad": self.response
        }
        return render(request, self.template_name, self.context)

class DetailTipoSeveridad(generic.View):
    template_name = "fallas/detail_tipo_severidad.html"
    context = {}
    url_base = f"http://localhost:8000/api/{API_URL}/v1/tipo_severidad/"
    response = None

    def get(self, request, pk):
        self.url_base += f"{pk}/"
        self.response = requests.get(self.url_base).json()
        self.context = {
            "tipo_severidad": self.response
        }
        return render(request, self.template_name, self.context)

class CreateTipoSeveridad(generic.View):
    template_name = "fallas/create_tipo_severidad.html"
    context = {}
    url_base = f"http://localhost:8000/api/{API_URL}/v1/tipo_severidad/create/"
    response = None
    payload = {}
    form_class = forms.CrearTipoSeveridad

    def get(self, request):
        self.context = {
            "form": self.form_class()
        }
        return render(request, self.template_name, self.context)

    def post(self, request):
        codigo = request.POST["codigo"]
        nombre = request.POST["nombre"]
        descripcion = request.POST["descripcion"]
        self.payload = {
            "codigo": codigo,
            "nombre": nombre,
            "descripcion": descripcion
        }

        response = requests.post(self.url_base, data=self.payload)

        return redirect("fallas:list_tipos_severidad")

class UpdateTipoSeveridad(generic.View):
    template_name = "fallas/update_tipo_severidad.html"
    context = {}
    url_get = f"http://localhost:8000/api/{API_URL}/v1/tipo_severidad/"
    url_put = f"http://localhost:8000/api/{API_URL}/v1/tipo_severidad/update/"
    response = None
    payload = {}

    def get(self, request, pk):
        self.url_get += f"{pk}/"
        self.response = requests.get(self.url_get).json()
        self.context = {
            "tipo_severidad": self.response
        }
        return render(request, self.template_name, self.context)

    def post(self, request, pk):
        self.url_put += f"{pk}/"
        self.payload = {
            "codigo": request.POST.get("codigo"),
            "nombre": request.POST.get("nombre"),
            "descripcion": request.POST.get("descripcion")
        }

        self.response = requests.put(url=self.url_put, data=self.payload).json()
        self.context = {
            "tipo_severidad": self.response
        }
        return redirect("fallas:list_tipos_severidad")

#---------------------------------------------------------------------------
#------------EDO REPORTE ---------------------------------------------------
#---------------------------------------------------------------------------
class ListEdoReporte(generic.View):
    template_name = "fallas/list_edo_reporte.html"
    context = {}
    url_base = f"http://localhost:8000/api/{API_URL}/v1/edo_reporte/list/"
    response = None

    def get(self, request):
        self.response = requests.get(self.url_base).json()
        self.context = {
            "edos_reporte": self.response
        }
        return render(request, self.template_name, self.context)

class DetailEdoReporte(generic.View):
    template_name = "fallas/detail_edo_reporte.html"
    context = {}
    url_base = f"http://localhost:8000/api/{API_URL}/v1/edo_reporte/"
    response = None

    def get(self, request, pk):
        self.url_base += f"{pk}/"
        self.response = requests.get(self.url_base).json()
        self.context = {
            "edo_reporte": self.response
        }
        return render(request, self.template_name, self.context)

class CreateEdoReporte(generic.View):
    template_name = "fallas/create_edo_reporte.html"
    context = {}
    url_base = f"http://localhost:8000/api/{API_URL}/v1/edo_reporte/create/"
    response = None
    payload = {}
    form_class = forms.CrearEdoReporte

    def get(self, request):
        self.context = {
            "form": self.form_class()
        }
        return render(request, self.template_name, self.context)

    def post(self, request):
        codigo = request.POST["codigo"]
        nombre = request.POST["nombre"]
        descripcion = request.POST["descripcion"]
        self.payload = {
            "codigo": codigo,
            "nombre": nombre,
            "descripcion": descripcion
        }

        response = requests.post(self.url_base, data=self.payload)

        return redirect("fallas:list_edos_reporte")

class UpdateEdoReporte(generic.View):
    template_name = "fallas/update_edo_reporte.html"
    context = {}
    url_get = f"http://localhost:8000/api/{API_URL}/v1/edo_reporte/"
    url_put = f"http://localhost:8000/api/{API_URL}/v1/edo_reporte/update/"
    response = None
    payload = {}

    def get(self, request, pk):
        self.url_get += f"{pk}/"
        self.response = requests.get(self.url_get).json()
        self.context = {
            "edo_reporte": self.response
        }
        return render(request, self.template_name, self.context)

    def post(self, request, pk):
        self.url_put += f"{pk}/"
        self.payload = {
            "codigo": request.POST.get("codigo"),
            "nombre": request.POST.get("nombre"),
            "descripcion": request.POST.get("descripcion")
        }

        self.response = requests.put(url=self.url_put, data=self.payload).json()
        self.context = {
            "edo_reporte": self.response
        }
        return redirect("fallas:list_edos_reporte")

#---------------------------------------------------------------------------
#------------TIPO REPORTE --------------------------------------------------
#---------------------------------------------------------------------------
class ListTipoReporte(generic.View):
    template_name = "fallas/list_tipo_reporte.html"
    context = {}
    url_base = f"http://localhost:8000/api/{API_URL}/v1/tipo_reporte/list/"
    response = None

    def get(self, request):
        self.response = requests.get(self.url_base).json()
        self.context = {
            "tipos_reporte": self.response
        }
        return render(request, self.template_name, self.context)

class DetailTipoReporte(generic.View):
    template_name = "fallas/detail_tipo_reporte.html"
    context = {}
    url_base = f"http://localhost:8000/api/{API_URL}/v1/tipo_reporte/"
    response = None

    def get(self, request, pk):
        self.url_base += f"{pk}/"
        self.response = requests.get(self.url_base).json()
        self.context = {
            "tipo_reporte": self.response
        }
        return render(request, self.template_name, self.context)

class CreateTipoReporte(generic.View):
    template_name = "fallas/create_tipo_reporte.html"
    context = {}
    url_base = f"http://localhost:8000/api/{API_URL}/v1/tipo_reporte/create/"
    response = None
    payload = {}
    form_class = forms.CrearTipoReporte

    def get(self, request):
        self.context = {
            "form": self.form_class()
        }
        return render(request, self.template_name, self.context)

    def post(self, request):
        tipo_falla_id = request.POST["tipo_falla"]
        reporte_falla_id = request.POST["reporte_falla"]
        self.payload = {
            "tipo_falla": tipo_falla_id,
            "reporte_falla": reporte_falla_id
        }

        response = requests.post(self.url_base, data=self.payload)

        return redirect("fallas:list_tipos_reporte")

class UpdateTipoReporte(generic.View):
    template_name = "fallas/update_tipo_reporte.html"
    context = {}
    url_get = f"http://localhost:8000/api/{API_URL}/v1/tipo_reporte/"
    url_put = f"http://localhost:8000/api/{API_URL}/v1/tipo_reporte/update/"
    response = None
    payload = {}

    def get(self, request, pk):
        self.url_get += f"{pk}/"
        self.response = requests.get(self.url_get).json()
        self.context = {
            "tipo_reporte": self.response
        }
        return render(request, self.template_name, self.context)

    def post(self, request, pk):
        self.url_put += f"{pk}/"
        self.payload = {
            "tipo_falla": request.POST.get("tipo_falla"),
            "reporte_falla": request.POST.get("reporte_falla")
        }

        self.response = requests.put(url=self.url_put, data=self.payload).json()
        self.context = {
            "tipo_reporte": self.response
        }
        return redirect("fallas:list_tipos_reporte")

#---------------------------------------------------------------------------
#------------REPORTE FALLA -------------------------------------------------
#---------------------------------------------------------------------------
class ListReporteFalla(generic.View):
    template_name = "fallas/list_reporte_falla.html"
    context = {}
    url_base = f"http://localhost:8000/api/{API_URL}/v1/reportes/list/"
    response = None

    def get(self, request):
        self.response = requests.get(self.url_base).json()
        self.context = {
            "reportes_falla": self.response
        }
        return render(request, self.template_name, self.context)

class DetailReporteFalla(generic.View):
    template_name = "fallas/detail_reporte_falla.html"
    context = {}
    url_base = f"http://localhost:8000/api/{API_URL}/v1/reportes/"
    response = None

    def get(self, request, pk):
        self.url_base += f"{pk}/"
        self.response = requests.get(self.url_base).json()
        self.context = {
            "reporte_falla": self.response
        }
        return render(request, self.template_name, self.context)
    
class CreateReporteFalla(generic.View):
    template_name = "fallas/create_reporte_falla.html"
    context = {}
    url_base = f"http://localhost:8000/api/{API_URL}/v1/reportes/create/"
    response = None
    payload = {}
    form_class = forms.CrearReporteFalla

    def get(self, request):
        self.context = {
            "form": self.form_class()
        }
        return render(request, self.template_name, self.context)

    def post(self, request):
        asunto = request.POST["asunto"]
        fecharesolucion = request.POST["fecharesolucion"]
        fechacreacion = request.POST["fechacreacion"]
        horacreacion = request.POST["horacreacion"]
        tiempoparo = request.POST.get("tiempoparo", None)
        causaraiz = request.POST["causaraiz"]
        descripcion = request.POST.get("descripcion", "")
        imagen = request.POST.get("imagen", "")
        maquina_id = request.POST.get("maquina", None)
        trabajador_id = request.POST.get("trabajador", None)
        tipo_falla_id = request.POST.get("tipo_falla", None)
        tipo_severidad_id = request.POST.get("tipo_severidad", None)

        self.payload = {
            "asunto": asunto,
            "fecharesolucion": fecharesolucion,
            "fechacreacion": fechacreacion,
            "horacreacion": horacreacion,
            "tiempoparo": tiempoparo,
            "causaraiz": causaraiz,
            "descripcion": descripcion,
            "imagen": imagen,
            "maquina": maquina_id,
            "trabajador": trabajador_id,
            "tipo_falla": tipo_falla_id,
            "tipo_severidad": tipo_severidad_id
        }

        response = requests.post(self.url_base, data=self.payload)

        return redirect("fallas:list_reportes")

class UpdateReporteFalla(generic.View):
    template_name = "fallas/update_reporte_falla.html"
    context = {}
    url_get = f"http://localhost:8000/api/{API_URL}/v1/reportes/"
    url_put = f"http://localhost:8000/api/{API_URL}/v1/reportes/update/"
    response = None
    payload = {}

    def get(self, request, pk):
        self.url_get += f"{pk}/"
        self.response = requests.get(self.url_get).json()
        self.context = {
            "reporte_falla": self.response
        }
        return render(request, self.template_name, self.context)

    def post(self, request, pk):
        self.url_put += f"{pk}/"
        self.payload = {
            "asunto": request.POST.get("asunto"),
            "fecharesolucion": request.POST.get("fecharesolucion"),
            "fechacreacion": request.POST.get("fechacreacion"),
            "horacreacion": request.POST.get("horacreacion"),
            "tiempoparo": request.POST.get("tiempoparo"),
            "causaraiz": request.POST.get("causaraiz"),
            "descripcion": request.POST.get("descripcion"),
            "imagen": request.POST.get("imagen"),
            "maquina": request.POST.get("maquina"),
            "trabajador": request.POST.get("trabajador"),
            "tipo_falla": request.POST.get("tipo_falla"),
            "tipo_severidad": request.POST.get("tipo_severidad")
        }

        self.response = requests.put(url=self.url_put, data=self.payload).json()
        self.context = {
            "reporte_falla": self.response
        }
        return redirect("fallas:list_reportes")
    
