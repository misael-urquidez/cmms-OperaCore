# Guía de diseño de módulos Django
## OperaCore CMMS - Cómo diseñar vistas rápidas y sin latencia

Este documento resume el diagnóstico de latencia hecho sobre el módulo de Fallas y el patrón de diseño que debe replicarse en el resto de los módulos del proyecto (usuarios, mantenimiento, inventario, maquinaria, indicadores, elipse y los que se agreguen después). Está pensado para el equipo humano y también como referencia para cuando se use IA para generar o revisar código Django en este proyecto.

---

## 1. Arquitectura del proyecto

El proyecto está dividido en dos servidores Django independientes que se comunican por HTTP:

* **`client/` (puerto 8001):** renderiza el HTML. No toca la base de datos directo.
* **`api/` (puerto 8000):** expone endpoints REST (Django REST Framework) y sí toca la base de datos.

Cada vista del `client` que necesita datos hace una llamada HTTP síncrona al `api` usando la librería `requests`, espera la respuesta, y hasta entonces renderiza el template. Esto significa que la latencia percibida por el usuario al navegar es, casi siempre, la suma de las llamadas HTTP que la vista hace antes de poder responder.

> **Regla de oro:** si una vista del `client` tarda, casi nunca es un problema del navegador ni del HTML; es la vista de Django bloqueada esperando al `api`. Ahí es donde hay que mirar primero.

---

## 2. Causas de latencia encontradas (caso real)

* **Llamadas secuenciales en vez de una sola:** una vista pedía 4 catálogos con 4 `requests.get()` uno tras otro, sumando 4 round-trips antes de renderizar.
* **Vistas sin caché:** una lista pegaba al `api` en cada carga de página, sin excepción.
* **TTL de caché demasiado corto** en datos que no necesitan estar 100% al segundo (ej. 30 seg para un catálogo de máquinas), provocando *refetch* constante.
* **Sin manejo de errores:** si el `api` no respondía, la vista tronaba con un 500 en vez de degradar con un aviso.
* **Sin reuso de conexión:** cada `requests.get()`/`post()` abre una conexión TCP nueva contra el `api` en vez de reusar una existente.
* **Caché de archivos (`FileBasedCache`)** en vez de un backend en memoria (no es lo más grave, pero no es lo estándar en producción).

---

## 3. Patrón obligatorio para toda vista que consuma el api/

Cualquier vista nueva en `client/apps/<modulo>/views.py` que necesite datos del `api` debe seguir estos 4 puntos, en este orden de prioridad:

### 3.1 Un solo endpoint agregador si necesitas más de 1 dato

Si una pantalla necesita 2 o más catálogos/listas para renderizar, no se hacen 2+ llamadas desde el `client`. Se crea un endpoint en el `api` que junta todo en una sola respuesta (patrón *Backend-for-Frontend*). Esto convierte N round-trips en 1.

```python
# api/apps/<modulo>/views.py
class CatalogosXAPIView(APIView):
    # Junta en una sola respuesta todo lo que la pantalla X necesita.
    def get(self, request):
        data = {
            "catalogo_a": SerializerA(ModeloA.objects.all(), many=True).data,
            "catalogo_b": SerializerB(ModeloB.objects.all(), many=True).data,
        }
        return Response(data, status=status.HTTP_200_OK)

# api/apps/<modulo>/urls.py
path("v1/catalogos-x/", views.CatalogosXAPIView.as_view(), name="catalogos-x"),
```

### 3.2 Sesión HTTP compartida (reuso de conexión)

En vez de `requests.get(...)`/`requests.post(...)` sueltos, define una sesión a nivel de módulo y úsala en toda la vista:

```python
import requests
from django.conf import settings

# una vez por proceso, se reusa en cada request
API_URL = f"{settings.API_BASE_URL}/<modulo>"
SESSION = requests.Session()

# uso:
SESSION.get(f"{API_URL}/algo/", timeout=5)
SESSION.post(f"{API_URL}/algo/", json=payload, timeout=5)
```

### 3.3 Caché + try/except, siempre juntos

Ninguna llamada al `api` va sin caché y sin manejo de error. La plantilla estándar:

```python
from django.core.cache import cache
import requests

MI_TTL = 30  # ver tabla de TTLs recomendados (sección 4)

def _cargar_datos():
    datos = cache.get("mi_modulo_datos")
    if datos is not None:
        return datos, True
    try:
        datos = SESSION.get(f"{API_URL}/v1/algo/", timeout=5).json()
    except requests.exceptions.RequestException:
        return None, False
    
    cache.set("mi_modulo_datos", datos, MI_TTL)
    return datos, True

class MiVista(generic.View):
    template_name = "mi_modulo/pantalla.html"
    
    def get(self, request):
        datos, ok = _cargar_datos()
        if not ok:
            messages.warning(request, "No se pudo conectar con la API.")
            datos = []
        return render(request, self.template_name, {"datos": datos})
```

### 3.4 Invalidar el caché al escribir, no solo esperar el TTL

Cuando una vista crea/edita/borra algo (POST/PUT/DELETE contra el `api`), borra la entrada de caché correspondiente justo después de que la escritura tenga éxito, para que la siguiente lectura salga fresca sin esperar el TTL completo:

```python
if response.status_code == 201:
    cache.delete("mi_modulo_datos")
    messages.success(request, "Registrado correctamente")
    return redirect("mi_modulo:lista")
```

---

## 4. TTLs de caché recomendados

| Tipo de dato | TTL sugerido | Por qué |
| :--- | :--- | :--- |
| **Catálogos casi estáticos**<br>*(roles, tipos, severidades, estados)* | 2-10 min | Casi nunca cambian |
| **Catálogos que se dan de alta seguido**<br>*(máquinas, usuarios nuevos)* | 30 seg | Necesitan aparecer rápido, pero no en cada request |
| **Listas / reportes** | 10-15 seg | Cambian seguido, pero no hace falta al segundo |
| **Status/ping de módulos** | 30 seg | Es solo un indicador, no dato crítico |
| **Respuestas de chat / IA**<br>*(ej. Elipse)* | Sin caché | Cada pregunta es única, no tiene sentido cachear |

---

## 5. Backend de caché

El proyecto usa actualmente `FileBasedCache`. Funciona, pero no es el estándar de producción porque usa *locking* de archivos y no escala bien entre varios workers. Cuando se despliegue a producción, cambiar a **Redis**:

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
    }
}
```

---

## 6. Checklist antes de dar por terminado un módulo

Antes de hacer merge de un módulo nuevo o una vista nueva, revisar:

- [ ] ¿Esta pantalla necesita más de 1 dato del api? ¿ya se creó un endpoint agregador en vez de varias llamadas sueltas?
- [ ] ¿La vista usa una `Session()` de módulo en vez de `requests.get/post` sueltos?
- [ ] ¿Toda lectura (GET al api) pasa primero por `cache.get()`?
- [ ] ¿El TTL elegido tiene sentido según la tabla de la sección 4?
- [ ] ¿Toda llamada a requests está en un `try/except requests.exceptions.RequestException`?
- [ ] ¿Si el api no responde, la vista degrada con un `messages.warning(...)` en vez de tronar con 500?
- [ ] ¿Toda escritura (POST/PUT/DELETE) que afecta un dato cacheado hace `cache.delete(...)` del key correspondiente al terminar?
- [ ] ¿Se evitó cachear cosas que cambian por request (ej. respuestas de chat/IA, datos de sesión de usuario)?

---

## 7. Instrucciones para cuando se use IA para generar código Django

Si alguien del equipo le pide a una IA (Claude, Copilot, ChatGPT, etc.) que genere o modifique una vista en `client/apps/<modulo>/views.py`, pegar este contexto en el prompt para que el código generado ya venga bien desde el principio:

> "Este proyecto Django (`client`) NO toca la base de datos directo; consume otro proyecto Django (`api`) por HTTP usando `requests`. Cualquier vista que agregues debe:
> 1. Usar una `requests.Session()` de módulo en vez de `requests.get/post` sueltos.
> 2. Si necesita más de un dato del api, primero revisar si conviene crear un endpoint agregador en el api en vez de hacer varias llamadas desde el client.
> 3. Pasar toda lectura por `django.core.cache` antes de golpear el api, con un TTL acorde a qué tan seguido cambia el dato.
> 4. Envolver toda llamada `requests` en `try/except requests.exceptions.RequestException` y degradar con `messages.warning` en vez de dejar que la vista truene.
> 5. Invalidar (`cache.delete`) el key correspondiente después de cualquier escritura exitosa contra el api."

Esto evita el error más común al generar vistas Django con IA: el modelo por default genera `requests.get()` sueltos, sin caché y sin manejo de errores, porque es el patrón "tutorial" más común en su entrenamiento, no porque sea la forma correcta de hacerlo en un proyecto con dos servidores separados como este.

---

## 8. Errores comunes a evitar

* **Poner TIMEOUT larguísimos "para que no truene":** mejor un timeout corto (3-5 seg) + caché + mensaje de error claro.
* **Cachear datos que dependen del usuario logueado usando una key genérica compartida entre todos los usuarios** (fuga de datos entre sesiones).
* **TTLs de 0 o negativos "para que siempre esté fresco":** eso es lo mismo que no tener caché.
* **Repetir la misma llamada al api en 2 vistas distintas con 2 keys de caché distintas** cuando podrían compartir la misma key (como pasó entre el dashboard de usuarios y la lista de fallas).
* **Meter lógica de negocio (cálculos, validaciones fuertes) en el client:** el client solo debe orquestar la llamada al api y renderizar; la lógica pesada vive en el api.

---

*Documento generado a partir del diagnóstico de latencia del módulo Fallas OperaCore CMMS.*
