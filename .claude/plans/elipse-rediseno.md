# Rediseño de Elipse: animaciones + memoria

Hacer que el módulo Elipse se sienta pulido (animaciones sutiles, texto que se
escribe, estados de carga) y que recuerde: historial persistente entre sesiones
+ datos personales del usuario como contexto.

## Decisiones tomadas

- **Memoria**: historial persistente **y** memoria de datos personales.
- **Almacenamiento**: `localStorage` del navegador. Cero migraciones, cero
  cambios en la BD (todos los modelos son `managed = False`, el esquema MySQL
  es fijo — meter una tabla nueva rompería ese contrato).
- **Animaciones**: elegantes y sutiles (200–400ms, estilo ChatGPT/Claude).

## Contexto relevante

- El proyecto **no tiene ni una sola animación** hoy (`grep @keyframes` = 0).
  Esto establece la convención para el resto del CMMS.
- Los temas se manejan con tokens CSS sobre `body[data-theme]`
  (oscuro / `light` / `plain`) más colores inline que inyecta `theme.js`.
  Todo lo nuevo debe usar `var(--color-primary)`, `var(--color-surface)`, etc.
  y verse bien en los tres temas.
- `client/` es un proxy sin estado hacia `api/`; el `api/` tiene el motor.
- Elipse solo está enlazado desde `base_admin.html:88`, no desde `base_tecni`.

---

## Archivos

| Archivo | Acción |
|---|---|
| `client/static/css/elipse.css` | **nuevo** — estilos + keyframes del módulo |
| `client/static/js/elipse.js` | **nuevo** — chat, animaciones, memoria |
| `client/templates/elipse/index.html` | reescribir (adelgazar: hoy trae 60 líneas de `<style>` y 90 de `<script>` inline) |
| `client/static/css/admin.css` | quitar el bloque `.elipse-*` (líneas ~452-490), se muda a `elipse.css` |
| `api/apps/elipse/views.py` | aceptar `memoria` en el POST e inyectarla en los prompts |

---

## Parte 1 — Animaciones

### 1.1 Keyframes base (`elipse.css`)

Todas envueltas en un guard de accesibilidad:

```css
@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
}
```

| Animación | Uso | Duración |
|---|---|---|
| `elipse-msg-in` | burbuja entra: `opacity 0→1` + `translateY(8px→0)` | 320ms `cubic-bezier(.22,.61,.36,1)` |
| `elipse-dot` | 3 puntos de «pensando», desfasados 160ms | 1.2s loop |
| `elipse-row-in` | filas de tabla en cascada (`animation-delay: calc(var(--i) * 40ms)`) | 260ms |
| `elipse-card-pop` | stat-cards con `scale(.96→1)` | 300ms |
| `elipse-chip-in` | chips de bienvenida, escalonados | 240ms |

### 1.2 Efecto de escritura

El backend devuelve **HTML ya armado** (`_tabla()`, `_cards()`), no texto plano.
Así que no se puede hacer `typewriter` ingenuo sobre el string — rompería las
etiquetas a media palabra.

Solución: parsear la respuesta en un `<template>` y recorrer sus hijos:

- Nodos de texto dentro de `<p>` / `<li>` → se escriben carácter por carácter
  (~18ms/char, con `requestAnimationFrame`, tope de ~1.8s por bloque).
- Nodos estructurales (`<table>`, `.stat-cards`, `<details>`) → aparecen de golpe
  con su propia animación de entrada (cascada / pop).

Un click en cualquier parte del chat o la tecla `Esc` **salta la animación** y
pinta todo de inmediato (importante: nadie quiere esperar a que se escriba una
tabla de 50 filas).

### 1.3 Estados de carga

Reemplaza el botón deshabilitado actual por:

```
Elipse
┌─────────────────────────┐
│ ● ● ●   consultando…    │
└─────────────────────────┘
```

El texto del estado cambia según lo que esté pasando: `pensando…` →
`consultando la base de datos…` → `buscando en internet…`. Se decide con un
timer local (a los 900ms y 2.5s), ya que el API responde de una sola vez.

### 1.4 Detalles de pulido

- **Textarea que crece** con el contenido (hasta 6 líneas) en vez de `rows="1"` fijo.
- **Botón de enviar** que muta a ícono de stop mientras carga.
- **Auto-scroll inteligente**: solo baja si ya estabas hasta abajo; si subiste a
  leer, aparece un botón flotante «↓ nuevos mensajes».
- **Orbe ⚡ de bienvenida** con un `breathe` lento (4s), muy tenue.
- **Botón del sidebar** con el `⚡` en un pulso sutil.

---

## Parte 2 — Memoria

### 2.1 Historial persistente

`localStorage['elipse_historial_v1']` — array de `{role, content, html, ts}`.

- Se guarda después de cada intercambio.
- Al cargar la página se rehidrata **sin animación** (aparece ya pintado) y con
  un separador `— conversación anterior —`.
- Tope de 40 mensajes (se descartan los más viejos) para no reventar el cupo de
  ~5MB de localStorage.
- Botón **«Nueva conversación»** en la cabecera que limpia y vuelve a la
  pantalla de bienvenida.

### 2.2 Memoria de datos personales

`localStorage['elipse_memoria_v1']` — array de `{id, texto, ts}`, máx. 20.

**Cómo se llena** (dos vías):

1. **Explícita** — el usuario escribe `recuerda que ...` / `acuérdate que ...`.
   Se detecta con regex en el cliente, se guarda, y Elipse confirma con un
   toast `🧠 Anotado.` sin gastar una llamada a la IA.
2. **Automática** — no se hace. Que la IA decida sola qué guardar es
   impredecible y difícil de depurar; se deja fuera a propósito.

**Cómo se usa**: en cada POST el cliente manda `memoria: [...]`. El API la
inyecta al `SYSTEM_PROMPT` como un bloque:

```
Datos que el usuario te pidió recordar:
- Soy técnico de la línea 3
- Mi máquina asignada es MAQ003
```

**Panel de memoria**: un botón 🧠 en la cabecera abre un panel lateral que
lista lo recordado, con una ✕ para borrar cada dato. Sin esto la memoria es
una caja negra — el usuario tiene que poder ver y editar lo que guardó.

### 2.3 Cambios en el API

En `api/apps/elipse/views.py`:

- `ElipseChatAPIView.post` lee `request.data.get('memoria', [])`.
- Nueva función `_bloque_memoria(memoria)` que la formatea (con tope de 20
  entradas × 200 chars, para que no crezca sin control).
- Se concatena a `SYSTEM_PROMPT` y a `SYSTEM_ADMIN` en `_ai_con_sql()` y a los
  prompts de `_resolver_busqueda_web()`.
- Los intents locales (`_resolve`) **no** la usan — son SQL fijo, no hay IA que
  contextualizar.

---

## Parte 3 — Bugs que arreglo de paso

Dos cosas que vi al leer el módulo y que caen dentro de lo que voy a tocar:

1. **XSS almacenado** en `_tabla()` (`views.py:255`): `'<td>%s</td>' % v`
   inyecta valores de la BD sin escapar. Si la descripción de una falla trae
   `<script>`, se ejecuta. Fix: `html.escape(str(v))`. También aplica a
   `_badge()` y `_cards()`.
2. **Las preguntas rápidas están duplicadas** en Python (`views.py:48`) y en JS
   (`index.html:98`), con un comentario que admite el problema. Como voy a
   reescribir el template de todos modos: el API expone `GET /elipse/sugerencias/`
   y el JS las pide una vez. Una sola fuente de verdad.

No toco el `sql_puro` sin restricción de rol — es un tema aparte y más delicado
(hay que decidir qué rol puede), lo dejo señalado.

---

## Orden de trabajo

1. `elipse.css` — keyframes y estilos (incluye mover el bloque de `admin.css`).
2. `elipse.js` — render animado, typewriter, memoria, auto-scroll.
3. `index.html` — reescribir apoyado en los dos anteriores.
4. `api/views.py` — `memoria` en prompts, endpoint de sugerencias, escapado HTML.
5. Verificar en los 3 temas (oscuro / claro / plano) y con sidebar colapsado.

## Cómo se verifica

Levantar `api` (8000) y `client` (8001), entrar a `/elipse/` y comprobar:

- Mensaje entra con fade+slide; los puntos laten mientras carga.
- El texto se escribe; una tabla entra en cascada; click salta la animación.
- Recargar la página → el historial sigue ahí.
- `recuerda que trabajo en la línea 3` → aparece en el panel 🧠; preguntar algo
  después y ver que la respuesta lo toma en cuenta.
- Cambiar de tema en el modal de configuración → todo sigue legible.
- Con el `api` apagado → el error de conexión también se anima, no rompe.
