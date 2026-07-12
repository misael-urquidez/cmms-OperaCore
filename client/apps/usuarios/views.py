import requests
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import generic

API_URL = f"{settings.API_BASE_URL}/usuarios"

# Roles y especialidades casi nunca cambian, asi que los cacheamos para no
# pegarle al api/ en cada carga del login. TTL de 10 min. Para forzar un
# refresco inmediato hay un comando en comandos.txt (o reinicia el server).
CATALOGOS_TTL = 60 * 10


def _cargar_catalogos():
    """Devuelve (roles, especialidades, ok). Los toma del cache si estan;
    si no, los pide al api/ y los guarda. ok=False si el api/ no respondio."""
    roles = cache.get("usuarios_roles")
    especialidades = cache.get("usuarios_especialidades")
    if roles is not None and especialidades is not None:
        return roles, especialidades, True

    try:
        roles = requests.get(f"{API_URL}/roles/", timeout=5).json()
        especialidades = requests.get(f"{API_URL}/especialidades/", timeout=5).json()
    except requests.exceptions.RequestException:
        return [], [], False

    cache.set("usuarios_roles", roles, CATALOGOS_TTL)
    cache.set("usuarios_especialidades", especialidades, CATALOGOS_TTL)
    return roles, especialidades, True


class AuthView(generic.View):
    """Pantalla de acceso: login + registro en la misma vista, con pestañas.
    De paso jala los catalogos de rol/especialidad para el <select> del
    formulario de registro."""

    template_name = "usuarios/index.html"

    def get(self, request):
        if request.session.get("usuario"):
            return redirect("home")

        tab = request.GET.get("tab", "login")
        roles, especialidades, ok = _cargar_catalogos()
        if not ok:
            messages.warning(request, "No se pudieron cargar los catálogos de rol/especialidad (¿está corriendo el api/?).")

        return render(
            request,
            self.template_name,
            {"tab": tab, "roles": roles, "especialidades": especialidades},
        )


class LoginView(generic.View):
    """Procesa el login: identificador puede ser correo o usuario."""

    def post(self, request):
        identificador = request.POST.get("identificador", "").strip()
        password = request.POST.get("password", "")
        volver = f"{reverse('usuarios:index')}?tab=login"

        if not identificador or not password:
            messages.error(request, "Ingresa tu usuario/correo y tu contraseña.")
            return redirect(volver)

        try:
            response = requests.post(
                f"{API_URL}/login/",
                json={"identificador": identificador, "password": password},
                timeout=5,
            )
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el servidor. Intenta más tarde.")
            return redirect(volver)

        if response.status_code != 200:
            try:
                detalle = response.json().get("detail", "Usuario/correo o contraseña incorrectos.")
            except ValueError:
                detalle = "Usuario/correo o contraseña incorrectos."
            messages.error(request, detalle)
            return redirect(volver)

        trabajador = response.json()
        request.session["usuario"] = trabajador
        messages.success(request, f"Bienvenido, {trabajador.get('nombre') or trabajador.get('usuario')}.")
        return redirect("home")


class RegistroView(generic.View):
    """Procesa el alta de un TRABAJADOR nuevo."""

    def post(self, request):
        payload = {
            "nombre": request.POST.get("nombre", "").strip(),
            "apellidoPat": request.POST.get("apellidoPat", "").strip(),
            "apellidoMat": request.POST.get("apellidoMat", "").strip() or None,
            "telefono": request.POST.get("telefono", "").strip(),
            "correo": request.POST.get("correo", "").strip(),
            "usuario": request.POST.get("usuario", "").strip(),
            "password": request.POST.get("password", ""),
            "password2": request.POST.get("password2", ""),
            "rol": request.POST.get("rol") or None,
            "especialidad": request.POST.get("especialidad") or None,
        }
        volver = f"{reverse('usuarios:index')}?tab=registro"

        try:
            response = requests.post(f"{API_URL}/registro/", json=payload, timeout=5)
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con el servidor. Intenta más tarde.")
            return redirect(volver)

        if response.status_code == 201:
            messages.success(request, "Cuenta creada. Ya puedes iniciar sesión.")
            return redirect(f"{reverse('usuarios:index')}?tab=login")

        try:
            errores = response.json()
        except ValueError:
            errores = {"error": "No se pudo crear la cuenta."}

        for campo, detalle in errores.items():
            detalle_txt = detalle[0] if isinstance(detalle, list) else detalle
            messages.error(request, f"{campo}: {detalle_txt}")
        return redirect(volver)


class LogoutView(generic.View):
    def get(self, request):
        request.session.flush()
        messages.success(request, "Sesión cerrada.")
        return redirect("home")