import requests
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.http import JsonResponse
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

        # Si venimos de un registro fallido, esto trae los errores por campo
        # y lo que la persona ya habia escrito (menos las contraseñas). Se
        # leen UNA sola vez con session.pop (igual que los messages de
        # Django) para no repoblar el formulario en cargas posteriores.
        errores_campos = request.session.pop("registro_errores", {})
        valores_campos = request.session.pop("registro_valores", {})

        # Si el error NO fue en "rol", quiere decir que la clave de
        # seguridad ya paso la validacion del api/ (si hubiera sido
        # invalida, el registro se habria rechazado por eso primero). No
        # tiene caso volver a pedirla: se deja desbloqueado.
        desbloquear_campos = bool(valores_campos) and "rol" not in errores_campos

        return render(
            request,
            self.template_name,
            {
                "tab": tab,
                "roles": roles,
                "especialidades": especialidades,
                "errores_campos": errores_campos,
                "valores_campos": valores_campos,
                "desbloquear_campos": desbloquear_campos,
            },
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

        # Normaliza cada error a lista (el api/ ya los manda asi via DRF,
        # pero por si acaso), para que el template pueda usar
        # errores_campos.<campo>.0 sin sorpresas.
        errores = {
            campo: (detalle if isinstance(detalle, list) else [detalle])
            for campo, detalle in errores.items()
        }

        # Se guardan en sesion (patron "flash", igual que los messages de
        # Django): el siguiente GET los lee una sola vez y los usa para
        # marcar en rojo el campo exacto que fallo + no perder lo que la
        # persona ya habia escrito. Las contraseñas NUNCA se guardan aqui.
        request.session["registro_errores"] = errores
        request.session["registro_valores"] = {
            campo: valor for campo, valor in payload.items()
            if campo not in ("password", "password2") and valor is not None
        }

        # "error"/"detail" son claves genericas del api/ (no corresponden a
        # ningun input del formulario): esas si se muestran completas en el
        # banner de arriba. El resto ya se ve marcado en su campo, asi que
        # arriba solo se avisa que hay que revisar.
        genericos = [errores[k][0] for k in ("error", "detail") if k in errores]
        if genericos:
            for msg in genericos:
                messages.error(request, msg)
        else:
            messages.error(request, "Revisa los campos marcados en rojo.")
        return redirect(volver)


class ValidarClaveRolView(generic.View):
    """Proxy AJAX llamado por auth.js mientras el usuario escribe la clave
    de seguridad en el registro. Reenvia al api/ (roles/validar/) y regresa
    el mismo JSON tal cual: {"valido": bool, "nombre": str|None}.

    Es un proxy (y no se llama al api/ directo desde el navegador) porque
    asi el api/ no necesita exponerse publicamente al front, igual que el
    resto de las vistas de esta app."""

    def get(self, request):
        codigo = request.GET.get("codigo", "").strip()
        if not codigo:
            return JsonResponse({"valido": False, "nombre": None})

        try:
            response = SESSION.get(
                f"{API_URL}/roles/validar/", params={"codigo": codigo}, timeout=5
            )
            data = response.json()
        except (requests.exceptions.RequestException, ValueError):
            return JsonResponse({"valido": False, "nombre": None, "error": True}, status=502)

        return JsonResponse(data)


class LogoutView(generic.View):
    def get(self, request):
        request.session.flush()
        messages.success(request, "Sesión cerrada.")
        return redirect("usuarios:index")


class ConfigPerfilView(generic.View):
    """Guarda los cambios del modal de Configuracion -> Cuenta. Llamada por
    fetch() desde navbar.js, responde JSON. Pega de verdad al api/ (PATCH a
    v1/trabajadores/<numeroNomina>/).

    Quien puede editar que, segun el rol en sesion (esto se vuelve a
    verificar aqui, NO solo se confia en que el formulario del front ya
    haya deshabilitado los campos):
    - ADMIN: nombre, apellidoPat, apellidoMat, correo, telefono, usuario,
      contraseña y foto.
    - Cualquier otro rol (p.ej. TECNI): SOLO usuario y contraseña. Si llega
      cualquier otro campo en el POST, se ignora sin avisar (no es un
      error del usuario, es que el front para su rol ni siquiera manda
      esos inputs).

    Para la foto (cualquier rol, incluido TECNI, puede cambiar/quitar la suya):
    - si llega un archivo en 'foto' -> se manda tal cual al api/, que
      reemplaza el archivo anterior.
    - si llega 'eliminar_foto=1' (y no hay archivo nuevo) -> se le indica
      al api/ que borre la foto actual.

    Para la contraseña (cualquier rol):
    - solo se manda si 'password' viene con contenido; se exige ademas
      'password2' identico (el front ya valida esto, pero se repite aqui
      por si alguien pega directo al endpoint).
    """

    CAMPOS_SOLO_ADMIN = ("nombre", "apellidoPat", "apellidoMat", "correo", "telefono")

    def post(self, request):
        usuario = request.session.get("usuario")
        if not usuario:
            return JsonResponse(
                {"ok": False, "errores": {"detail": "Tu sesión expiró, vuelve a iniciar sesión."}},
                status=401,
            )

        es_admin = usuario.get("rol") == "ADMIN"
        numero_nomina = usuario.get("numeroNomina")
        payload = {}

        if es_admin:
            for campo in self.CAMPOS_SOLO_ADMIN:
                payload[campo] = request.POST.get(campo, "").strip()

        usuario_nuevo = request.POST.get("usuario", "").strip()
        if not usuario_nuevo:
            return JsonResponse(
                {"ok": False, "errores": {"usuario": "El usuario es obligatorio."}},
                status=400,
            )
        payload["usuario"] = usuario_nuevo

        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")
        if password or password2:
            if password != password2:
                return JsonResponse(
                    {"ok": False, "errores": {"password2": "Las contraseñas no coinciden."}},
                    status=400,
                )
            if len(password) < 8:
                return JsonResponse(
                    {"ok": False, "errores": {"password": "Debe tener al menos 8 caracteres."}},
                    status=400,
                )
            payload["password"] = password
            payload["password2"] = password2

        files_payload = {}
        foto_file = request.FILES.get("foto")
        if foto_file:
            files_payload["foto"] = (foto_file.name, foto_file.read(), foto_file.content_type)
        elif request.POST.get("eliminar_foto") == "1":
            payload["eliminar_foto"] = "true"

        try:
            response = SESSION.patch(
                f"{API_URL}/v1/trabajadores/{numero_nomina}/",
                data=payload,
                files=files_payload if files_payload else None,
                timeout=10,
            )
        except requests.exceptions.RequestException:
            return JsonResponse(
                {"ok": False, "errores": {"detail": "No se pudo conectar con el servidor. Intenta más tarde."}},
                status=502,
            )

        if response.status_code != 200:
            try:
                errores = response.json()
            except ValueError:
                errores = {"detail": "No se pudieron guardar los cambios."}
            return JsonResponse({"ok": False, "errores": errores}, status=response.status_code)

        # El api/ regresa solo los campos editables (no numeroNomina, rol_nombre,
        # etc.), asi que se combinan con lo que ya habia en sesion.
        usuario.update(response.json())
        request.session["usuario"] = usuario
        request.session.modified = True

        return JsonResponse({"ok": True, "usuario": usuario})


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

        # Máquinas: total y operativas.
        try:
            maquinas = SESSION.get(
                f"{settings.API_BASE_URL}/monitoreo/maquinas/", timeout=3
            ).json()
            stats["maquinas"] = len(maquinas)
            stats["maquinas_operativas"] = sum(
                1 for m in maquinas if m.get("estado_maquina") == "OPERA"
            )
        except (requests.RequestException, ValueError):
            pass

        # Órdenes activas: cualquiera que no esté cerrada o cancelada.
        try:
            ordenes = SESSION.get(
                f"{settings.API_BASE_URL}/mantenimiento/v1/ordenes/list/", timeout=3
            ).json()
            stats["ordenes_activas"] = sum(
                1 for o in ordenes if o.get("estado_orden") not in ("CERRA", "CANCE")
            )
        except (requests.RequestException, ValueError):
            pass

        # Trabajadores: total y activos.
        try:
            trabajadores = SESSION.get(
                f"{settings.API_BASE_URL}/fallas/v1/trabajadores/", timeout=3
            ).json()
            stats["trabajadores"] = len(trabajadores)
            stats["trabajadores_activos"] = sum(
                1 for t in trabajadores if t.get("actividad")
            )
        except (requests.RequestException, ValueError):
            pass

        # Indicadores clave (RF-26): MTBF/MTTR/disponibilidad por maquina
        # (tabla), ordenes pendientes y alertas de inventario (tarjetas).
        indicadores_maquinas = []
        try:
            resumen = SESSION.get(
                f"{settings.API_BASE_URL}/indicadores/v1/resumen/", timeout=3
            ).json()
            indicadores_maquinas = resumen.get("por_maquina", [])
            stats["ordenes_pendientes"] = resumen.get("ordenes_pendientes")
            stats["alertas_inventario"] = resumen.get("alertas_inventario")
        except (requests.RequestException, ValueError):
            pass

        return render(
            request,
            self.template_name,
            {
                "seccion": "dashboard",
                "stats": stats,
                "ultimas_fallas": ultimas_fallas,
                "indicadores_maquinas": indicadores_maquinas,
            }
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

        # Ordenes programadas asignadas a este tecnico (no todas las activas,
        # solo las que estan en estado PROGRAMADA y le pertenecen a el).
        try:
            ordenes = SESSION.get(
                f"{settings.API_BASE_URL}/mantenimiento/v1/ordenes/list/", timeout=3
            ).json()
            stats["ordenes_activas"] = sum(
                1 for o in ordenes
                if o.get("trabajador") == usuario.get("numeroNomina")
                and o.get("estado_orden") == "PROGR"
            )
        except (requests.RequestException, ValueError):
            pass

        return render(
            request,
            self.template_name,
            {"seccion": "dashboard", "stats": stats, "ultimas_fallas": ultimas_fallas},
        )