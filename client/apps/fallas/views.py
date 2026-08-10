import datetime
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.http import HttpResponse
from django.views import generic
from django.contrib import messages
import requests
from urllib.parse import quote
from django.conf import settings
from django.core.cache import cache


API_URL = f"{settings.API_BASE_URL}/fallas"

# Sesion HTTP a nivel de modulo: se crea una vez y reusa la conexion TCP
# con el api/ en vez de abrir una nueva por cada request (menos latencia).
SESSION = requests.Session()

# Severidad, tipo de falla y estados casi no cambian: cache de 2 min.
# Maquinas se da de alta más seguido, asi que su cache es mucho mas corto
# (30 seg) para que una maquina nueva aparezca casi al instante.
# La lista de reportes cambia seguido pero no necesitas verla al segundo:
# 15 seg. El dashboard de usuarios comparte este mismo cache.
CATALOGOS_TTL = 60 * 2
MAQUINAS_TTL = 30
REPORTES_TTL = 15


def _cargar_catalogos():
    """Devuelve (severidades, tipos_falla, maquinas, estados, trabajadores, ok).
    Los toma del cache si estan todos; si falta alguno, pide todos juntos en
    UNA sola llamada al endpoint agregador del api/ y los vuelve a cachear
    cada uno con su propio TTL."""
    severidades = cache.get("fallas_severidades")
    tipos_falla = cache.get("fallas_tipos_falla")
    maquinas = cache.get("fallas_maquinas")
    estados = cache.get("fallas_estados")
    trabajadores = cache.get("fallas_trabajadores")

    if None not in (severidades, tipos_falla, maquinas, estados, trabajadores):
        return severidades, tipos_falla, maquinas, estados, trabajadores, True

    try:
        data = SESSION.get(f"{API_URL}/v1/catalogos-reporte/", timeout=5).json()
    except requests.exceptions.RequestException:
        return [], [], [], [], [], False

    severidades = data["severidades"]
    tipos_falla = data["tipos_falla"]
    maquinas = data["maquinas"]
    estados = data["estados"]
    trabajadores = data.get("trabajadores", [])

    cache.set("fallas_severidades", severidades, CATALOGOS_TTL)
    cache.set("fallas_tipos_falla", tipos_falla, CATALOGOS_TTL)
    cache.set("fallas_maquinas", maquinas, MAQUINAS_TTL)
    cache.set("fallas_estados", estados, CATALOGOS_TTL)
    cache.set("fallas_trabajadores", trabajadores, CATALOGOS_TTL)

    return severidades, tipos_falla, maquinas, estados, trabajadores, True

class ReporteFalla(generic.View):
    template_name = "fallas/reporte_falla.html"
    context = {}
    url_create = f"{API_URL}/v2/reportes/create/"

    def _contexto_base(self, request):
        usuario = request.session.get("usuario")
        severidades, tipos_falla, maquinas, estados, trabajadores, ok = _cargar_catalogos()
        if not ok:
            messages.warning(request, "No se pudo conectar con la API para cargar los catálogos.")

        # Filtrar solo máquinas operativas para la selección en el formulario
        maquinas_operativas = [m for m in maquinas if str(m.get("estado_maquina", "")).upper() == "OPERA" or str(m.get("estado", "")).upper() == "OPERA"]

        return {
            "severidades": severidades,
            "tipos_falla": tipos_falla,
            "maquinas": maquinas_operativas if maquinas_operativas else maquinas,
            "seccion": "fallas",
            "subseccion": "reporte",
            "usuario": usuario,
            "base_template": "base_tecni.html" if usuario.get("rol") == "TECNI" else "base_admin.html",
        }

    def get(self, request):
        usuario = request.session.get("usuario")
        if not usuario:
            messages.warning(request, "Inicia sesión para continuar.")
            return redirect("usuarios:index")

        self.context = self._contexto_base(request)
        return render(request, self.template_name, self.context)

    def post(self, request):
        usuario = request.session.get("usuario")
        if not usuario:
            messages.warning(request, "Inicia sesión para continuar.")
            return redirect("usuarios:index")

        tiempo_paro_raw = request.POST.get("tiempoParo")
        try:
            tiempo_paro = float(tiempo_paro_raw) if tiempo_paro_raw else 0.0
        except ValueError:
            tiempo_paro = 0.0

        fecha_resolucion = request.POST.get("fechaSolucion")
        if not fecha_resolucion or fecha_resolucion.strip() == "":
            fecha_resolucion = None

        # Forzamos estado "ABIER" y el trabajador tomando de la sesión
        self.payload = {
            "asunto": request.POST.get("asunto", "").strip(),
            "descripcion": request.POST.get("descripcion", "").strip(),
            "causaRaiz": request.POST.get("causaRaiz", "").strip(),
            "tiempoParo": tiempo_paro,
            "fechaResolucion": fecha_resolucion,
            "maquina": request.POST.get("maquina"),
            "trabajador": usuario.get("numeroNomina"),
            "tipo_severidad": request.POST.get("tipo_severidad"),
            "estado_reporte": "ABIER",
        }

        tipo_falla_ids = []
        valor_base = request.POST.get("tipo_falla")
        if valor_base and valor_base.isdigit():
            tipo_falla_ids.append(int(valor_base))

        idx = 1
        while True:
            val = request.POST.get(f"tipo_falla_{idx}")
            if val is None:
                break
            if val and val.isdigit():
                tipo_falla_ids.append(int(val))
            idx += 1

        self.payload["tipo_falla_ids"] = tipo_falla_ids

        archivo = request.FILES.get("imagen")
        files = {"imagen": (archivo.name, archivo.read(), archivo.content_type)} if archivo else None

        try:
            self.response = SESSION.post(
                url=self.url_create,
                data=self.payload,
                files=files,
                timeout=10
            )
        except requests.exceptions.RequestException:
            messages.warning(request, "No se pudo conectar con la API para registrar el reporte.")
            return self._render_error(request)

        if self.response.status_code == 201:
            cache.delete("fallas_reportes_list")
            creado = self.response.json()
            messages.success(request, "El reporte de falla ha sido registrado correctamente.")
            
            from urllib.parse import quote
            return redirect(
                "{}?levantar_orden=1&reporte={}&asunto={}&maquina={}".format(
                    reverse("fallas:lista"),
                    creado.get("numeroRegistro"),
                    quote(creado.get("asunto") or ""),
                    quote(self.payload.get("maquina") or ""),
                )
            )
        else:
            try:
                detalle = self.response.json()
            except ValueError:
                detalle = self.response.text
            messages.warning(request, f"Error al registrar el reporte: {detalle}")
            return self._render_error(request)

    def _render_error(self, request):
        context = self._contexto_base(request)
        context["datos"] = self.payload
        return render(request, self.template_name, context)
    
class ListTipoFalla(generic.View):
    template_name = "fallas/list_tipo_falla.html"
    context = {}
    url_base = f"{API_URL}/v1/tipo_falla/list/"
    response = None

class ListaReportes(generic.View):
    template_name = "fallas/lista_reportes.html"
    url_base = f"{API_URL}/v1/reportes/list/"

    def get(self, request):
        usuario = request.session.get("usuario")
        if not usuario:
            messages.warning(request, "Inicia sesión para continuar.")
            return redirect("usuarios:index")

        try:
            reportes = SESSION.get(url=self.url_base, timeout=5).json()
            cache.set("fallas_reportes_list", reportes, REPORTES_TTL)
        except (requests.exceptions.RequestException, ValueError):
            reportes = []
            messages.warning(request, "No se pudo conectar con la API para cargar los reportes.")

        from .views import _cargar_catalogos
        severidades, tipos_falla, maquinas, estados, trabajadores, _ = _cargar_catalogos()

        # Extraer los códigos de máquina presentes en los reportes
        codigos_maquinas_con_falla = set()
        for r in reportes:
            # Revisa la clave exacta que devuelve la API para la máquina
            cod = r.get("maquina") or r.get("maquina_codigo")
            if isinstance(cod, dict):
                cod = cod.get("codigo")
            if cod:
                codigos_maquinas_con_falla.add(str(cod))

        # Filtrar la lista de máquinas para incluir solo las que tienen al menos un reporte
        maquinas_con_reportes = [
            m for m in maquinas 
            if str(m.get("codigo")) in codigos_maquinas_con_falla
        ]

        # Mapeo de estados sin ENATE ni CERRA
        MAPA_ESTADOS = {
            "ABIER": "Abierto",
            "CANCE": "Cancelado",
            "ENESP": "En espera",
            "RESUE": "Resuelto"
        }

        MAPA_SEVERIDADES = {
            "ALTA": "Alta",
            "MEDIA": "Media",
            "BAJA": "Baja",
            "CRITI": "Crítica"
        }

        hoy = datetime.date.today()

        mes_str = request.GET.get("mes")
        if mes_str:
            try:
                anio_sel, mes_sel = map(int, mes_str.split("-"))
            except ValueError:
                anio_sel, mes_sel = hoy.year, hoy.month
                mes_str = f"{hoy.year}-{hoy.month:02d}"
        else:
            anio_sel, mes_sel = hoy.year, hoy.month
            mes_str = f"{hoy.year}-{hoy.month:02d}"

        # Contadores ajustados
        kpi_totales = len(reportes)
        kpi_espera = 0
        kpi_abiertos = 0
        kpi_cancelados = 0
        kpi_resueltos = 0

        anio_str = request.GET.get("anio", str(hoy.year))
        try:
            anio_grafica = int(anio_str)
        except ValueError:
            anio_grafica = hoy.year

        total_fallas_meses = [0] * 12

        for r in reportes:
            raw_est = (
                r.get("estado_reporte") or 
                r.get("estado_reporte_codigo") or 
                r.get("estado_reporte_nombre") or
                r.get("estado")
            )

            if isinstance(raw_est, dict):
                raw_est = raw_est.get("codigo") or raw_est.get("nombre")

            code_est = str(raw_est or "").strip().upper()
            nombre_estado = MAPA_ESTADOS.get(code_est, code_est.capitalize() if code_est else "Abierto")

            r["estado_evaluado"] = nombre_estado
            r["estado_reporte_nombre"] = nombre_estado

            raw_sev = r.get("tipo_severidad_nombre") or r.get("tipo_severidad")
            if isinstance(raw_sev, dict):
                raw_sev = raw_sev.get("codigo") or raw_sev.get("nombre")

            code_sev = str(raw_sev or "").strip().upper()
            nombre_sev = MAPA_SEVERIDADES.get(code_sev, str(raw_sev or "Crítica").capitalize())

            r["severidad_evaluada"] = nombre_sev
            r["tipo_severidad_nombre"] = nombre_sev

            # Conteos Generales
            if code_est in ["ENESP", "EN ESPERA"]:
                kpi_espera += 1
            elif code_est in ["ABIER", "ABIERTO"]:
                kpi_abiertos += 1

            # Conteos y datos de gráfica por fecha
            fecha_val = r.get("fechaCreacion")
            if fecha_val:
                try:
                    f_str = str(fecha_val)[:10]
                    f_creac = datetime.datetime.strptime(f_str, "%Y-%m-%d").date()

                    if f_creac.year == anio_sel and f_creac.month == mes_sel:
                        if code_est in ["CANCE", "CANCELADO"]:
                            kpi_cancelados += 1
                        elif code_est in ["RESUE", "RESUELTO"]:
                            kpi_resueltos += 1

                    if f_creac.year == anio_grafica:
                        m_idx = f_creac.month - 1
                        total_fallas_meses[m_idx] += 1

                except ValueError:
                    pass

        context = {
            "reportes": reportes,
            "severidades": severidades,
            "maquinas": maquinas_con_reportes,
            "estados": estados,
            "seccion": "fallas",
            "subseccion": "lista",
            "usuario": usuario,
            "base_template": "base_tecni.html" if usuario.get("rol") == "TECNI" else "base_admin.html",
            "kpi_totales": kpi_totales,
            "kpi_espera": kpi_espera,
            "kpi_abiertos": kpi_abiertos,
            "kpi_cancelados": kpi_cancelados,
            "kpi_resueltos": kpi_resueltos,
            "mes_actual": mes_str,
            "anio_actual": anio_grafica,
            "grafica_data": total_fallas_meses,
            "anios_disponibles": [hoy.year, hoy.year - 1, hoy.year - 2],
        }
        return render(request, self.template_name, context)
    

class DetailReporte(generic.View):
    template_name = "fallas/fallas-modal/ver-detalle.html"
    context = {}

    def get(self, request, pk):
        cache_key = f"fallas_reporte_{pk}"
        reporte = cache.get(cache_key)

        if reporte is None:
            try:
                resp = SESSION.get(f"{API_URL}/v1/reportes/{pk}/", timeout=5)
                if resp.status_code != 200:
                    return render(request, self.template_name, {"reporte": None})
                reporte = resp.json()
                cache.set(cache_key, reporte, 30)
            except (requests.exceptions.RequestException, ValueError):
                return render(request, self.template_name, {"reporte": None})

        self.context = {"reporte": reporte}
        return render(request, self.template_name, self.context)

class ActualizarReporte(generic.View):
    template_name = "fallas/actualizar_reporte.html"

    def _cargar_reporte(self, request, pk):
        cache_key = f"fallas_reporte_{pk}"
        reporte = cache.get(cache_key)
        if reporte is not None:
            return reporte
        try:
            resp = SESSION.get(f"{API_URL}/v1/reportes/{pk}/", timeout=5)
            if resp.status_code != 200:
                messages.warning(request, "No se pudo cargar el reporte.")
                return None
            reporte = resp.json()
            cache.set(cache_key, reporte, 30)
            return reporte
        except (requests.exceptions.RequestException, ValueError):
            messages.warning(request, "No se pudo conectar con la API.")
            return None

    def _contexto(self, request, reporte):
        severidades, tipos_falla, maquinas, estados, trabajadores, _ = _cargar_catalogos()
        return {
            "reporte": reporte,
            "severidades": severidades,
            "tipos_falla": tipos_falla,
            "maquinas": maquinas,
            "estados": estados,
            "trabajadores": trabajadores,
            "usuario": request.session.get("usuario"),
            "base_template": "base_tecni.html" if request.session.get("usuario", {}).get("rol") == "TECNI" else "base_admin.html",
        }

    def get(self, request, pk):
        usuario = request.session.get("usuario")
        if not usuario:
            messages.warning(request, "Inicia sesión para continuar.")
            return redirect("usuarios:index")

        reporte = self._cargar_reporte(request, pk)
        if reporte is None:
            return redirect("fallas:lista")

        return render(request, self.template_name, self._contexto(request, reporte))

    def post(self, request, pk):
        usuario = request.session.get("usuario")
        if not usuario:
            messages.warning(request, "Inicia sesión para continuar.")
            return redirect("usuarios:index")

        # Obtener datos del formulario
        nuevo_estado = request.POST.get("estado_reporte")
        codigo_maquina = request.POST.get("maquina")

        payload = {
            "asunto": request.POST.get("asunto"),
            "descripcion": request.POST.get("descripcion"),
            "causaRaiz": request.POST.get("causaRaiz"),
            "tiempoParo": request.POST.get("tiempoParo"),
            "fechaResolucion": request.POST.get("fechaSolucion") or None,
            "maquina": codigo_maquina,
            "trabajador": request.POST.get("trabajador"),
            "tipo_severidad": request.POST.get("tipo_severidad"),
            "estado_reporte": nuevo_estado,
        }

        tipo_falla_ids = []
        valor_base = request.POST.get("tipo_falla")
        if valor_base:
            tipo_falla_ids.append(int(valor_base))
        idx = 1
        while True:
            val = request.POST.get(f"tipo_falla_{idx}")
            if val is None:
                break
            if val:
                tipo_falla_ids.append(int(val))
            idx += 1
        payload["tipo_falla_ids"] = tipo_falla_ids

        archivo = request.FILES.get("imagen")
        files = {"imagen": archivo} if archivo else None

        # -----------------------------------------------------------------
        # LÓGICA DE CAMBIO DE ESTADO DE LA MÁQUINA
        # -----------------------------------------------------------------
        reporte_previo = self._cargar_reporte(request, pk)
        estado_anterior = reporte_previo.get("estado_reporte") if reporte_previo else None

        nuevo_estado_maquina = None
        if nuevo_estado == "CANCE" and estado_anterior != "CANCE":
            nuevo_estado_maquina = "ESPER"
        elif nuevo_estado == "ABIER" and estado_anterior != "ABIER":
            nuevo_estado_maquina = "FALLO"

        if nuevo_estado_maquina and codigo_maquina:
            try:
                url_maquina = f"{settings.API_BASE_URL}/maquinaria/v1/maquina/update/{codigo_maquina}/"

                if nuevo_estado_maquina == "ESPER":
                    # 1. Obtener estado actual de la máquina desde la API
                    url_detail = f"{settings.API_BASE_URL}/maquinaria/v1/maquina/{codigo_maquina}/"
                    res_det = SESSION.get(url_detail, timeout=5)
                    estado_actual_maq = None
                    
                    if res_det.status_code == 200:
                        det_data = res_det.json()
                        raw_edo = det_data.get("estado_maquina") or det_data.get("estado")
                        if isinstance(raw_edo, dict):
                            estado_actual_maq = raw_edo.get("codigo") or raw_edo.get("id")
                        else:
                            estado_actual_maq = raw_edo

                    # 2. Transición intermedia si la máquina está en FALLO
                    if estado_actual_maq == "FALLO":
                        SESSION.patch(url_maquina, json={"estado_maquina": "MANTE"}, timeout=5)

                    # 3. Transición final a ESPER
                    SESSION.patch(url_maquina, json={"estado_maquina": "ESPER"}, timeout=5)

                else:
                    # Para cambio a ABIER -> FALLO
                    SESSION.patch(url_maquina, json={"estado_maquina": "FALLO"}, timeout=5)

            except requests.exceptions.RequestException as e:
                logger.error(f"Error al actualizar estado de máquina {codigo_maquina}: {e}")

        # -----------------------------------------------------------------
        # ACTUALIZAR EL REPORTE
        # -----------------------------------------------------------------
        try:
            api_url = f"{API_URL}/v2/reportes/update/{pk}/"
            response = SESSION.patch(url=api_url, data=payload, files=files, timeout=10)
        except requests.exceptions.RequestException:
            messages.warning(request, "No se pudo conectar con la API para actualizar el reporte.")
            return self._render_error(request, pk, payload)

        if response.status_code == 200:
            # Borrar cachés relevantes
            cache.delete(f"fallas_reporte_{pk}")
            cache.delete("fallas_reportes_list")
            cache.delete("fallas_catalogos")
            cache.delete("catalogos")
            messages.success(request, "El reporte ha sido actualizado correctamente.")
            return redirect("fallas:lista")
        else:
            messages.warning(request, "Error al actualizar el reporte.")
            return self._render_error(request, pk, payload)


class InvalidarCacheReportes(generic.View):

    def post(self, request):
        cache.delete("fallas_reportes_list")
        return JsonResponse({"ok": True})


# ------------ EXPORTACIONES (proxy a la API) -------------------------
class _ExportarBase(generic.View):
    formato = None  # "csv", "xlsx", "pdf"

    def get(self, request, pk):
        try:
            resp = SESSION.get(f"{API_URL}/v1/reportes/{pk}/export/{self.formato}/", timeout=15)
        except requests.exceptions.RequestException:
            return HttpResponse("Error de conexion con la API", status=502)

        if resp.status_code != 200:
            return HttpResponse("Error al generar el archivo", status=resp.status_code)

        response = HttpResponse(resp.content, content_type=resp.headers.get("Content-Type", "application/octet-stream"))
        response["Content-Disposition"] = resp.headers.get("Content-Disposition", f'attachment; filename="reporte_falla_{pk}.{self.formato}"')
        return response


class ExportarReporteCSV(_ExportarBase):
    formato = "csv"


class ExportarReporteXLSX(_ExportarBase):
    formato = "xlsx"


class ExportarReportePDF(_ExportarBase):
    formato = "pdf"