import requests
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import generic

API_URL = f"{settings.API_BASE_URL}/usuarios"

# Sesion HTTP a nivel de modulo: se crea una vez y reusa la conexion TCP
# con el api/ en vez de abrir una nueva por cada request (menos latencia).
SESSION = requests.Session()

# Roles y especialidades casi nunca cambian, asi que los cacheamos para no
# pegarle al api/ en cada carga del login. TTL de 10 min. Para forzar un
# refresco inmediato hay un comando en comandos.txt (o reinicia el server).
CATALOGOS_TTL = 60 * 10
REPORTES_TTL = 15  # mismo TTL que usa fallas/views.py para la lista


def _cargar_catalogos():
    """Devuelve (roles, especialidades, ok). Los toma del cache si estan;
    si no, los pide al api/ y los guarda. ok=False si el api/ no respondio."""
    roles = cache.get("usuarios_roles")
    especialidades = cache.get("usuarios_especialidades")
    if roles is not None and especialidades is not None:
        return roles, especialidades, True

    try:
        roles = SESSION.get(f"{API_URL}/roles/", timeout=5).json()
        especialidades = SESSION.get(f"{API_URL}/especialidades/", timeout=5).json()
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
        usuario = request.session.get("usuario")
        if usuario:
            # Ya hay sesion: mandarlo a su pantalla segun rol.
            if usuario.get("rol") == "ADMIN":
                return redirect("usuarios:admin_dashboard")
            if usuario.get("rol") == "TECNI":
                return redirect("usuarios:tecni_dashboard")
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
            response = SESSION.post(
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

        # Redirigir segun el rol: ADMIN y TECNI a sus paneles; los demas
        # (ENCLN o sin rol) al home normal mientras desarrollamos sus menus.
        if trabajador.get("rol") == "ADMIN":
            return redirect("usuarios:admin_dashboard")
        if trabajador.get("rol") == "TECNI":
            return redirect("usuarios:tecni_dashboard")
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
            response = SESSION.post(f"{API_URL}/registro/", json=payload, timeout=5)
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
        return redirect("usuarios:index")


class AdminDashboardView(generic.View):
    """Panel principal del ADMINISTRADOR. Solo entra quien tiene sesion
    iniciada Y rol ADMIN; cualquier otro caso se regresa con aviso."""

    template_name = "usuarios/admin_dashboard.html"

    def get(self, request):
        usuario = request.session.get("usuario")
        if not usuario:
            messages.warning(request, "Inicia sesión para continuar.")
            return redirect("usuarios:index")

        if usuario.get("rol") != "ADMIN":
            messages.error(request, "No tienes permisos para entrar al panel de administración.")
            return redirect("home")

        # stats: por ahora solo fallas; aqui despues pegamos al api/ para
        # llenar el resto de las tarjetas (maquinas, ordenes, etc.).
        # La lista de reportes comparte cache con fallas/views.py: si alguien
        # visito "Ver reportes" hace menos de 15 seg, no volvemos a pegarle
        # al api/, usamos el mismo dato cacheado.
        stats = {}
        reportes = cache.get("fallas_reportes_list")
        if reportes is None:
            try:
                reportes = SESSION.get(
                    url=f"{settings.API_BASE_URL}/fallas/v1/reportes/list/", timeout=3
                ).json()
                cache.set("fallas_reportes_list", reportes, REPORTES_TTL)
            except (requests.RequestException, ValueError):
                # si la API no responde no tumbamos el dashboard, solo se
                # queda esa tarjeta/panel en su estado por defecto ("—").
                reportes = []
        stats["fallas_abiertas"] = len(reportes)
        ultimas_fallas = reportes[:5]

        return render(
            request,
            self.template_name,
            {"seccion": "dashboard", "stats": stats, "ultimas_fallas": ultimas_fallas},
        )


class TecniDashboardView(generic.View):
    """Panel principal del TECNICO. Solo entra quien tiene sesion iniciada Y
    rol TECNI; cualquier otro caso se regresa con aviso. Comparte el cache de
    la lista de fallas con AdminDashboardView/fallas para no duplicar llamadas
    al api/."""

    template_name = "usuarios/tecni_dashboard.html"

    def get(self, request):
        usuario = request.session.get("usuario")
        if not usuario:
            messages.warning(request, "Inicia sesión para continuar.")
            return redirect("usuarios:index")

        if usuario.get("rol") != "TECNI":
            messages.error(request, "No tienes permisos para entrar al panel de técnico.")
            return redirect("home")

        stats = {}
        reportes = cache.get("fallas_reportes_list")
        if reportes is None:
            try:
                reportes = SESSION.get(
                    url=f"{settings.API_BASE_URL}/fallas/v1/reportes/list/", timeout=3
                ).json()
                cache.set("fallas_reportes_list", reportes, REPORTES_TTL)
            except (requests.RequestException, ValueError):
                reportes = []
        stats["fallas_abiertas"] = len(reportes)
        ultimas_fallas = reportes[:5]

        return render(
            request,
            self.template_name,
            {"seccion": "dashboard", "stats": stats, "ultimas_fallas": ultimas_fallas},
        )