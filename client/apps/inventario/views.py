from datetime import date, datetime

import requests
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.views import generic

API_URL = f"{settings.API_BASE_URL}/inventario"

# Sesion HTTP a nivel de modulo: se crea una vez y reusa la conexion TCP
# con el api/ en vez de abrir una nueva por cada request.
SESSION = requests.Session()

# Refacciones y herramientas no cambian a cada rato: cache corto para
# no pegarle al api/ en cada click, pero que una entrada/salida nueva
# se refleje casi al instante.
REFACCIONES_TTL = 15
HERRAMIENTAS_TTL = 30


class ListadoInventario(generic.View):
    """Vista de listado: refacciones y herramientas, con alerta visual de stock bajo."""
    template_name = "inventario/list.html"

    def get(self, request):
        refacciones = cache.get("inventario_refacciones")
        if refacciones is None:
            try:
                refacciones = SESSION.get(f"{API_URL}/v1/refacciones/list/", timeout=5).json()
                cache.set("inventario_refacciones", refacciones, REFACCIONES_TTL)
            except (requests.exceptions.RequestException, ValueError):
                refacciones = []
                messages.warning(request, "No se pudo conectar con la API para cargar las refacciones.")

        herramientas = cache.get("inventario_herramientas")
        if herramientas is None:
            try:
                herramientas = SESSION.get(f"{API_URL}/v1/herramientas/list/", timeout=5).json()
                cache.set("inventario_herramientas", herramientas, HERRAMIENTAS_TTL)
            except (requests.exceptions.RequestException, ValueError):
                herramientas = []
                messages.warning(request, "No se pudo conectar con la API para cargar las herramientas.")

        return render(request, self.template_name, {
            "refacciones": refacciones,
            "herramientas": herramientas,
            "seccion": "inventario",
            "subseccion": "listado",
        })


class RegistrarMovimiento(generic.View):
    """Formulario para registrar una entrada o salida; el api/ actualiza el stock."""
    template_name = "inventario/movimiento_form.html"
    url_create = f"{API_URL}/v2/movimientos/create/"

    def _refacciones(self, request):
        refacciones = cache.get("inventario_refacciones")
        if refacciones is None:
            try:
                refacciones = SESSION.get(f"{API_URL}/v1/refacciones/list/", timeout=5).json()
                cache.set("inventario_refacciones", refacciones, REFACCIONES_TTL)
            except (requests.exceptions.RequestException, ValueError):
                refacciones = []
                messages.warning(request, "No se pudo conectar con la API para cargar las refacciones.")
        return refacciones

    def get(self, request):
        return render(request, self.template_name, {
            "refacciones": self._refacciones(request),
            "seccion": "inventario",
            "subseccion": "movimiento",
        })

    def post(self, request):
        payload = {
            "descripcion": request.POST.get("descripcion", ""),
            "fecha": date.today().isoformat(),
            "hora": datetime.now().time().isoformat(),
            "tipo_movimiento": request.POST.get("tipo_movimiento"),
            "refaccion": request.POST.get("refaccion"),
            "cantidad": request.POST.get("cantidad", 0),
        }

        try:
            response = SESSION.post(self.url_create, data=payload, timeout=10)
        except requests.exceptions.RequestException:
            messages.warning(request, "No se pudo conectar con la API para registrar el movimiento.")
            return render(request, self.template_name, {"refacciones": self._refacciones(request)})

        if response.status_code == 201:
            # invalidar cache: el nuevo stock debe verse de inmediato en el listado
            cache.delete("inventario_refacciones")
            tipo = payload["tipo_movimiento"]
            messages.success(request, f"Movimiento de {tipo.lower()} registrado correctamente.")
            return redirect("inventario:listado")

        # la API devuelve 400 con el detalle de validación (ej. stock insuficiente)
        try:
            detalle = response.json()
        except ValueError:
            detalle = {}
        mensaje = detalle.get("non_field_errors") or detalle.get("cantidad") or ["Error al registrar el movimiento."]
        messages.error(request, " ".join(str(m) for m in mensaje))
        return render(request, self.template_name, {"refacciones": self._refacciones(request)})