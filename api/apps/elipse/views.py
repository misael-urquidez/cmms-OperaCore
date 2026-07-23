"""
elipse_views (api) - Asistente Elipse para OperaCore CMMS. v2.0

Motor de intents local (sin gastar IA) sobre maquinaria, fallas, ordenes de
mantenimiento, inventario (refacciones/herramientas), trabajadores e
indicadores (MTTR/MTBF). Si el intent no se reconoce, cae a IA (Groq) que
genera SQL dinamico. Si no hay internet/API key, responde en modo guiado
con sugerencias en vez de un error crudo.

Como extender: agrega un "if has(...): return 'mi_intent'" en _intent() y
su bloque correspondiente "if intent == 'mi_intent':" en _resolve().
"""
import difflib
import json
import re
import urllib.request
import urllib.error

from django.conf import settings
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response


# ─────────────────────────────────────────────────────────
# Modelos de IA disponibles (Groq)
# ─────────────────────────────────────────────────────────
MODELOS_IA = {
    'groq-llama':   {'id': 'llama-3.3-70b-versatile', 'label': 'Llama 3.3 70B', 'desc': 'Potente y rapido'},
    'groq-llama-8': {'id': 'llama-3.1-8b-instant',    'label': 'Llama 3.1 8B',  'desc': 'Ultra rapido'},
}
MODELO_DEFAULT = 'groq-llama'

# ── Palabras que indican intencion de MODIFICAR la BD ─────
PALABRAS_MODIFICAR = [
    'borra', 'borrar', 'elimina', 'eliminar', 'delete', 'drop',
    'modifica', 'modificar', 'actualiza', 'actualizar', 'update',
    'cambia', 'cambiar', 'crea', 'crear', 'insert', 'anade', 'anadir',
    'agrega', 'agregar', 'registra', 'registrar', 'truncate', 'alter',
    'podrias borrar', 'puedes borrar', 'podrias eliminar', 'puedes eliminar',
]

# ─────────────────────────────────────────────────────────
# Consultas pre-default (funcionan 100% offline, sin Groq)
# ─────────────────────────────────────────────────────────
PREGUNTAS_RAPIDAS = [
    {'cat': 'Operacion',  'icon': '📊', 'label': 'Resumen general',       'q': 'Dame un resumen general'},
    {'cat': 'Operacion',  'icon': '🔴', 'label': 'Maquinas en falla',     'q': 'Que maquinas estan en falla'},
    {'cat': 'Operacion',  'icon': '🛠️', 'label': 'Maquinas en mantenimiento', 'q': 'Maquinas en mantenimiento'},
    {'cat': 'Fallas',     'icon': '⚠️', 'label': 'Fallas abiertas',       'q': 'Fallas abiertas'},
    {'cat': 'Fallas',     'icon': '🚨', 'label': 'Fallas criticas',       'q': 'Fallas criticas'},
    {'cat': 'Fallas',     'icon': '🏆', 'label': 'Top maquinas con fallas','q': 'Top 5 maquinas con mas fallas'},
    {'cat': 'Ordenes',    'icon': '📋', 'label': 'Ordenes pendientes',    'q': 'Ordenes de mantenimiento pendientes'},
    {'cat': 'Ordenes',    'icon': '⏰', 'label': 'Ordenes vencidas',      'q': 'Ordenes vencidas'},
    {'cat': 'Inventario', 'icon': '📦', 'label': 'Refacciones bajo stock','q': 'Refacciones con bajo stock'},
    {'cat': 'Inventario', 'icon': '🔧', 'label': 'Herramientas disponibles','q': 'Herramientas disponibles'},
    {'cat': 'Personal',   'icon': '👤', 'label': 'Trabajadores activos',  'q': 'Trabajadores activos'},
    {'cat': 'Info',       'icon': '🤖', 'label': '¿Que puedes hacer?',    'q': 'Que puedes hacer'},
]

# ─────────────────────────────────────────────────────────
# Textos institucionales
# ─────────────────────────────────────────────────────────
INFO_OPERACORE = """
<p><strong>⚙️ OperaCore CMMS</strong></p>
<p>Sistema de gestion de mantenimiento (CMMS) para planta industrial. Administra
<strong>maquinaria, ordenes de mantenimiento, reportes de falla, refacciones,
herramientas, trabajadores e indicadores</strong> (MTTR/MTBF) de la operacion.</p>
<p><strong>Elipse</strong> es el asistente de IA interno de OperaCore. Puede
responder preguntas en lenguaje natural o ejecutar SQL directo, consultando
la base de datos en tiempo real.</p>
"""

CAPACIDADES = """
<p><strong>🤖 ¿Que puedo hacer yo, Elipse?</strong></p>
<p>Soy el asistente de OperaCore. Aqui algunos ejemplos de lo que puedo hacer:</p>
<ul>
  <li>🔴 <em>"Maquinas en falla"</em> / <em>"maquina MAQ003"</em></li>
  <li>⚠️ <em>"Fallas abiertas"</em> / <em>"fallas criticas"</em> / <em>"falla del reporte 5"</em></li>
  <li>📋 <em>"Ordenes pendientes"</em> / <em>"orden OM-2026-002"</em> / <em>"ordenes vencidas"</em></li>
  <li>🏆 <em>"Top 5 maquinas con mas fallas"</em> / <em>"top tecnicos"</em></li>
  <li>📦 <em>"Refacciones con bajo stock"</em> / <em>"busca la refaccion rodamiento"</em></li>
  <li>🔧 <em>"Herramientas disponibles"</em></li>
  <li>👤 <em>"Trabajadores activos"</em> / <em>"busca al trabajador Juan Perez"</em></li>
  <li>📈 <em>"Indicadores de la maquina MAQ002"</em> — MTTR / MTBF / disponibilidad</li>
  <li>💻 SQL puro: escribe <code>SELECT ...</code> y lo corro directo</li>
</ul>
<p style="color:var(--color-muted, #94a3b8);font-size:12px;">
  ⚠️ Solo puedo <strong>consultar</strong> datos, nunca modificar ni borrar nada.
</p>
"""

# ─────────────────────────────────────────────────────────
# Schema para el generador de SQL dinamico (fallback IA)
# ─────────────────────────────────────────────────────────
SCHEMA = """
Base de datos MySQL "operacore" de un CMMS (mantenimiento industrial).

TABLAS PRINCIPALES:
- MAQUINA(codigo PK, numeroSerie, nombre, descripcion, fechaInstalacion,
  linea FK->LINEA.codigo, marca FK->MARCA.clave, modelo FK->MODELO.codigo,
  estado_maquina FK->EDO_MAQUINA.codigo, tipo_maquina FK->TIPO_MAQUINA.numeroRegistro)
- EDO_MAQUINA(codigo PK, nombre) -- OPERA=Operativa, ESPER=EnEspera, DESHA=Deshabilitada,
  MANTE=EnMantenimiento, FALLO=EnFalla
- LINEA(codigo PK, nombre, area FK->AREA.codigo)
- AREA(codigo PK, nombre, planta FK->PLANTA.codigo)
- PLANTA(codigo PK, nombre)
- MARCA(clave PK, nombre) -- OJO: PK se llama "clave", no "codigo"
- MODELO(codigo PK, nombre, marca FK)
- TIPO_MAQUINA(numeroRegistro PK, nombre)

- REPORTE_FALLA(numeroRegistro PK, asunto, fechaCreacion, horaCreacion,
  fechaResolucion, tiempoParo, causaRaiz, descripcion,
  maquina FK->MAQUINA.codigo, trabajador FK->TRABAJADOR.numeroNomina,
  tipo_severidad FK->TIPO_SEVERIDAD.codigo, estado_reporte FK->EDO_REPORTE.codigo)
- TIPO_SEVERIDAD(codigo PK, nombre) -- BAJA, MEDIA, ALTA, CRITI=Critica
- EDO_REPORTE(codigo PK, nombre) -- ABIER=Abierto, ENATE=EnAtencion, ENESP=EnEspera,
  RESUE=Resuelto, CERRA=Cerrado, CANCE=Cancelado
- TIPO_FALLA(numeroRegistro PK, nombre)
- TIPO_REPORTE(id PK, tipo_falla FK, reporte_falla FK) -- catalogo de tipos por reporte (N:M)

- ORDEN_MANTENIMIENTO(folio PK VARCHAR, descripcion, diagnostico, notas,
  fechaProgramada, fechaCreacion, horaCreacion, fechaCierre, horaCierre,
  horasIntervenidas, porcentaje, maquina FK->MAQUINA.codigo,
  trabajador FK->TRABAJADOR.numeroNomina, reporte_falla FK->REPORTE_FALLA.numeroRegistro,
  tipo_mantenimiento FK->TIPO_MANTENIMIENTO.codigo, estado_orden FK->ESTADO_ORDEN.codigo)
- ESTADO_ORDEN(codigo PK, nombre) -- SOLIC, APROB, PROGR, ENPRO=EnProgreso, ESESP,
  EJECU=Ejecutada, CERRA=Cerrada, CANCE=Cancelada, PENDI=Pendiente
- TIPO_MANTENIMIENTO(codigo PK, nombre) -- CORRE=Correctivo, PREVE=Preventivo,
  PREDI=Predictivo, EMER=Emergencia

- TRABAJADOR(numeroNomina PK VARCHAR, nombre, apellidoPat, apellidoMat, telefono,
  correo, usuario, actividad BOOLEAN, rol FK->ROL.codigo,
  especialidad FK->ESPECIALIDAD.numeroRegistro)
- ROL(codigo PK, nombre) -- ej TECNI=Tecnico, ADMIN, ENCLN=EncargadoLinea
- ESPECIALIDAD(numeroRegistro PK, nombre)

- REFACCION(numeroRegistro PK, nombre, codigoSku, puntoReorden, costo, stock,
  stockMinimo, proveedor FK->PROVEEDOR.codigo, tipo_refaccion FK->TIPO_REFACCION.numeroRegistro,
  clasificacion FK->CLASIFICACION.codigo)
- CLASIFICACION(codigo PK, nombre) -- ALTAC=AltaCriticidad, MECRI=MedianaCriticidad, BAJAC=BajaCriticidad
- PROVEEDOR(codigo PK, razonSocial, nombreComercial, telefono, email)
- HERRAMIENTA(numeroRegistro PK, nombre, tipo_herramienta FK->TIPO_HERRAMIENTA.numeroRegistro)
- ESTADO_HERRAMIENTA(herramienta FK, edo_herramienta FK->EDO_HERRAMIENTA.codigo, cantidad)
- EDO_HERRAMIENTA(codigo PK, nombre) -- DISPO=Disponible, ENRE=EnReparacion, ENUSO, BAJA
- PIEZA(numeroSerie PK, nombre, horasOperacion, tiempoVidaUtil,
  edo_pieza FK->EDO_PIEZA.codigo, maquina FK->MAQUINA.codigo, tipo_pieza FK)
- EDO_PIEZA(codigo PK, nombre) -- OPERA, DEGRA=Degradada, FALLI=Fallida, ENREH, BAJA

- INDICADOR(numeroRegistro PK, fechaInicio, fechaFin, mttr FLOAT, mtbf FLOAT,
  porcentajeDispo INT, maquina FK->MAQUINA.codigo)
- MOVIMIENTO(numeroRegistro PK, descripcion, fecha, hora, tipoMovimiento,
  orden_mantenimiento FK, refaccion FK, pieza FK)
- LECTURA_SENSOR(numeroRegistro PK, maquina FK, timestamp, origen, vibracion, golpe, temperatura)

JOINS TIPICOS:
- MAQUINA.estado_maquina -> EDO_MAQUINA.codigo
- MAQUINA.linea -> LINEA.codigo -> LINEA.area -> AREA.codigo -> AREA.planta -> PLANTA.codigo
- REPORTE_FALLA.maquina -> MAQUINA.codigo ; REPORTE_FALLA.trabajador -> TRABAJADOR.numeroNomina
- ORDEN_MANTENIMIENTO.maquina -> MAQUINA.codigo ; .trabajador -> TRABAJADOR.numeroNomina
- ORDEN_MANTENIMIENTO.reporte_falla -> REPORTE_FALLA.numeroRegistro
- REFACCION.clasificacion -> CLASIFICACION.codigo
- Nombre completo de trabajador: CONCAT(nombre,' ',apellidoPat,' ',COALESCE(apellidoMat,''))
"""

SYSTEM_PROMPT = (
    "Eres Elipse, el asistente de inteligencia artificial de OperaCore, un sistema "
    "de gestion de mantenimiento (CMMS) para una planta industrial. "
    "Solo respondes preguntas sobre: maquinas, fallas, ordenes de mantenimiento, "
    "refacciones, herramientas, trabajadores e indicadores de la planta. "
    "Puedes mantener conversacion breve de trabajo: saludos, agradecimientos, "
    "seguimientos usando el historial. Si preguntan algo fuera de ese contexto, "
    "declina amablemente. Responde en espanol, claro y conciso."
)

SQL_SYSTEM_PROMPT = (
    "Eres un generador de SQL MySQL para el panel interno de OperaCore CMMS. "
    "Genera UNA SOLA consulta SQL SELECT.\n\n"
    "REGLAS ABSOLUTAS:\n"
    "1. Devuelve UNICAMENTE el SQL puro. Sin explicaciones, sin markdown, sin ```.\n"
    "2. Solo SELECT. Jamas INSERT/UPDATE/DELETE/DROP/TRUNCATE.\n"
    "3. LIMIT 100 maximo.\n"
    "4. Alias de columnas en espanol descriptivo.\n"
    "5. NO_SQL si la pregunta es completamente ajena a la BD.\n"
    "6. Nombres completos: CONCAT(nombre,' ',apellidoPat,' ',COALESCE(apellidoMat,'')).\n"
    "7. Fechas relativas: CURDATE(), NOW(), DATE_SUB(), DATE_ADD(), INTERVAL.\n"
    "8. Busquedas por nombre: LOWER(campo) LIKE LOWER('%texto%').\n"
    "9. Los nombres de tabla y columna respetan mayusculas/minusculas tal cual el esquema.\n"
    "10. Si la pregunta es conversacional, de opinion, saludo o agradecimiento, "
    "devuelve NO_SQL.\n"
    + SCHEMA
)


# ─────────────────────────────────────────────────────────
# Utilidades
# ─────────────────────────────────────────────────────────

def _q(sql, params=None):
    with connection.cursor() as cur:
        cur.execute(sql, params or [])
        cols = [d[0] for d in cur.description]
        rows = []
        for r in cur.fetchall():
            row = {}
            for k, v in zip(cols, r):
                row[k] = v.isoformat() if hasattr(v, 'isoformat') else v
            rows.append(row)
    return cols, rows


BADGES = {
    'operativa': 'disponible', 'ejecutada': 'disponible', 'resuelto': 'disponible',
    'en falla': 'cancelado', 'cancelado': 'cancelado', 'cancelada': 'cancelado',
    'en mantenimiento': 'ruta', 'en progreso': 'ruta', 'en atencion': 'ruta', 'aprobada': 'ruta', 'programada': 'ruta',
    'deshabilitada': 'finalizado', 'cerrado': 'finalizado', 'cerrada': 'finalizado',
    'en espera': 'retrasado', 'pendiente': 'retrasado', 'solicitada': 'retrasado', 'abierto': 'retrasado',
}

def _badge(val):
    if val is None:
        return ''
    tr = str.maketrans('áéíóú', 'aeiou')
    cls = BADGES.get(str(val).lower().translate(tr), 'finalizado')
    return '<span class="badge %s">&#9679; %s</span>' % (cls, val)

def _dinero(val):
    try:
        return '$%s' % '{:,.2f}'.format(float(val))
    except Exception:
        return str(val) if val is not None else '-'

def _tabla(cols, rows, est=None, dinero=None, max_r=50):
    if not rows:
        return '<em>Sin resultados.</em>'
    est = est or []
    dinero = dinero or []
    vis = rows[:max_r]
    extra = len(rows) - len(vis)
    th = ''.join('<th>%s</th>' % c for c in cols)
    trs = []
    for row in vis:
        tds = []
        for c in cols:
            v = row.get(c)
            if c in est:
                tds.append('<td>%s</td>' % _badge(v))
            elif c in dinero:
                tds.append('<td>%s</td>' % _dinero(v))
            elif v is None:
                tds.append('<td>-</td>')
            else:
                tds.append('<td>%s</td>' % v)
        trs.append('<tr>%s</tr>' % ''.join(tds))
    nota = ('<p style="margin-top:6px;font-size:11px;color:var(--color-muted,#94a3b8)">... y %d filas mas.</p>' % extra) if extra else ''
    return '<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>%s' % (th, ''.join(trs), nota)

def _cards(items):
    parts = []
    for i in items:
        parts.append(
            '<div class="stat-card">'
            '<div class="s-label">%s</div>'
            '<div class="s-val">%s</div>'
            '<div class="s-sub">%s</div>'
            '</div>' % (i['label'], i['val'], i.get('sub', ''))
        )
    return '<div class="stat-cards">%s</div>' % ''.join(parts)

def _texto_a_html(text):
    if not text:
        return ''
    parts = []
    in_ul = False
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            if in_ul:
                parts.append('</ul>')
                in_ul = False
            continue
        if line.startswith('- ') or line.startswith('* '):
            if not in_ul:
                parts.append('<ul>')
                in_ul = True
            parts.append('<li>%s</li>' % line[2:])
        else:
            if in_ul:
                parts.append('</ul>')
                in_ul = False
            line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
            parts.append('<p>%s</p>' % line)
    if in_ul:
        parts.append('</ul>')
    return ''.join(parts)

def _chips_sugeridas(items):
    parts = []
    for it in items:
        q_attr = it['q'].replace('"', '&quot;')
        parts.append(
            '<button type="button" class="elipse-chip" onclick="elipseEnviarTexto(this.dataset.q)" '
            'data-q="%s">%s %s</button>' % (q_attr, it['icon'], it['label'])
        )
    return '<div class="elipse-chips">%s</div>' % ''.join(parts)

def _es_error_conexion(msg):
    if not msg:
        return False
    m = msg.lower()
    return any(x in m for x in (
        'no hay api key', 'timed out', 'timeout', 'connection', 'network',
        'name or service not known', 'temporarily unavailable', 'urlerror',
    ))

def _respuesta_sin_internet(pregunta):
    frases = [it['q'] for it in PREGUNTAS_RAPIDAS]
    cercana = difflib.get_close_matches(pregunta, frases, n=1, cutoff=0.35)
    sugerencia_html = ''
    if cercana:
        item = next(it for it in PREGUNTAS_RAPIDAS if it['q'] == cercana[0])
        sugerencia_html = (
            '<p style="margin-top:6px">¿Quizas quisiste decir '
            '<strong>%s %s</strong>?</p>' % (item['icon'], item['label'])
        )
    return (
        '<div class="elipse-offline">'
        '<p><strong>📡 Sin conexion a internet / IA no disponible</strong></p>'
        '<p>No pude generar una respuesta con IA, pero puedo seguir consultando '
        'la base de datos directamente. Prueba alguna de estas:</p>'
        '%s%s'
        '</div>' % (sugerencia_html, _chips_sugeridas(PREGUNTAS_RAPIDAS))
    )


# ─────────────────────────────────────────────────────────
# Extraccion de identificadores desde texto libre
# ─────────────────────────────────────────────────────────

def _extraer_codigo_maquina(q):
    m = re.search(r'\b(MAQ\d+)\b', q, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    m = re.search(r'maquina\s+([a-z0-9\-]{3,})', q, re.IGNORECASE)
    return m.group(1).upper() if m else None

def _extraer_folio_orden(q):
    m = re.search(r'\b(OM-\d{4}-\d+)\b', q, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    m = re.search(r'folio\s+([a-z0-9\-]+)', q, re.IGNORECASE)
    return m.group(1).upper() if m else None

def _extraer_numero_reporte(q):
    m = re.search(r'reporte\s*#?\s*(\d+)|falla\s*#?\s*(\d+)|numero\s+(\d+)', q, re.IGNORECASE)
    if m:
        return int(next(x for x in m.groups() if x))
    return None

def _extraer_top_n(q):
    m = re.search(r'top\s+(\d+)|los\s+(\d+)\s+(?:mejores|primeros|mas)|primeros\s+(\d+)', q)
    if m:
        return int(next(x for x in m.groups() if x))
    return None

def _extraer_nombre_propio(q, palabra_ancla):
    m = re.search(
        palabra_ancla + r'(?:a)?\s+(?:al?\s+)?([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)',
        q, re.IGNORECASE
    )
    return m.group(1).strip() if m else None


# ─────────────────────────────────────────────────────────
# Deteccion de intent
# ─────────────────────────────────────────────────────────

def _intent(q_orig):
    q = q_orig.lower()
    tr = str.maketrans('áéíóúñ', 'aeioun')
    q = q.translate(tr)

    def has(*ws):
        return any(w in q for w in ws)

    # SQL puro
    if re.match(r'^\s*SELECT\s+', q_orig.strip(), re.IGNORECASE):
        return 'sql_puro'

    # Intento de modificar BD
    for palabra in PALABRAS_MODIFICAR:
        if palabra in q:
            return 'solo_lectura'

    # Saludo / bienvenida guiada
    if has('hola', 'buenos dias', 'buenas tardes', 'buenas noches', 'buenas', 'hey',
           'que tal') and len(q.split()) <= 4:
        return 'saludo'

    if has('que puedes hacer', 'que sabes hacer', 'capacidades', 'ayuda', 'help', 'que haces'):
        return 'capacidades'
    if has('que es operacore', 'sobre operacore', 'info de operacore', 'quien eres'):
        return 'info_sistema'
    if has('resumen', 'panorama', 'como va todo', 'dashboard', 'estado general'):
        return 'resumen'

    # ── Maquinas ─────────────────────────────────────────────
    codigo_maq = _extraer_codigo_maquina(q_orig)
    if codigo_maq and has('maquina', 'maq'):
        if has('indicador', 'mttr', 'mtbf', 'disponibilidad'):
            return 'indicadores_maquina'
        return 'maquina_especifica'
    if has('maquina', 'maquinas') and has('falla', 'fallando', 'fallo'):
        return 'maquinas_en_falla'
    if has('maquina', 'maquinas') and has('mantenimiento'):
        return 'maquinas_en_mantenimiento'
    if has('maquina', 'maquinas') and has('operativa', 'disponible', 'funcionando'):
        return 'maquinas_operativas'
    if has('maquina', 'maquinas') and has('lista', 'todas', 'listar'):
        return 'maquinas_lista'
    if has('indicador', 'mttr', 'mtbf', 'disponibilidad'):
        return 'indicadores_general'

    # ── Fallas / reportes ───────────────────────────────────
    num_reporte = _extraer_numero_reporte(q_orig)
    if num_reporte is not None and has('falla', 'reporte'):
        return 'falla_especifica'
    if has('falla', 'fallas') and has('critica', 'criticas'):
        return 'fallas_criticas'
    if has('falla', 'fallas') and has('abierta', 'abiertas', 'sin atender', 'pendiente'):
        return 'fallas_abiertas'
    if has('falla', 'fallas') and (has('top', 'ranking', 'mas fallas', 'mas reportes') or _extraer_top_n(q)):
        return 'top_maquinas_fallas'
    if has('falla', 'fallas', 'reporte', 'reportes') and has('reciente', 'recientes', 'ultima', 'ultimas'):
        return 'fallas_recientes'

    # ── Ordenes de mantenimiento ────────────────────────────
    folio = _extraer_folio_orden(q_orig)
    if folio and has('orden'):
        return 'orden_especifica'
    if has('orden', 'ordenes') and has('vencida', 'vencidas', 'atrasada', 'atrasadas'):
        return 'ordenes_vencidas'
    if has('orden', 'ordenes') and has('pendiente', 'pendientes', 'abierta', 'abiertas'):
        return 'ordenes_pendientes'
    if has('orden', 'ordenes') and has('cerrada', 'cerradas', 'completada', 'completadas', 'terminada', 'terminadas'):
        return 'ordenes_cerradas'
    if has('tecnico', 'tecnicos') and (has('top', 'ranking', 'mas ordenes') or _extraer_top_n(q)):
        return 'top_tecnicos'
    if has('orden', 'ordenes') and has('de', 'del') and has('tecnico', 'trabajador'):
        return 'ordenes_de_tecnico'

    # ── Inventario ───────────────────────────────────────────
    if has('refaccion', 'refacciones') and has('stock bajo', 'bajo stock', 'poco stock', 'reponer', 'agotand'):
        return 'refacciones_bajo_stock'
    if has('refaccion', 'refacciones') and has('busca', 'buscar'):
        return 'refaccion_buscar'
    if has('herramienta', 'herramientas') and has('disponible', 'disponibles'):
        return 'herramientas_disponibles'

    # ── Trabajadores ─────────────────────────────────────────
    if has('trabajadores por rol', 'cuantos trabajadores'):
        return 'trabajadores_por_rol'
    if has('busca', 'buscar') and has('trabajador', 'tecnico'):
        return 'trabajador_buscar'
    if has('trabajador', 'trabajadores') and has('activo', 'activos', 'lista', 'listar'):
        return 'trabajadores_lista'

    return 'ai'


# ─────────────────────────────────────────────────────────
# Resolucion de intents (consultas directas, sin IA)
# ─────────────────────────────────────────────────────────

def _resolve(intent, pregunta):
    q = pregunta.lower()
    tr = str.maketrans('áéíóúñ', 'aeioun')
    q = q.translate(tr)

    if intent == 'saludo':
        grupos = {}
        for it in PREGUNTAS_RAPIDAS:
            grupos.setdefault(it['cat'], []).append(it)
        secciones = ''.join(
            '<p style="margin-top:10px;font-size:12px;color:var(--color-muted,#94a3b8)"><strong>%s</strong></p>%s'
            % (cat, _chips_sugeridas(items))
            for cat, items in grupos.items()
        )
        return (
            '<p><strong>👋 ¡Hola! Soy Elipse.</strong></p>'
            '<p>Puedo consultar maquinas, fallas, ordenes, inventario y trabajadores '
            'directo de la base de datos.</p>%s' % secciones
        )

    if intent == 'capacidades':
        return CAPACIDADES

    if intent == 'info_sistema':
        return INFO_OPERACORE

    # ── SQL puro ─────────────────────────────────────────────
    if intent == 'sql_puro':
        sql_usuario = pregunta.strip()
        if re.match(r'^\s*SELECT\s+', sql_usuario, re.IGNORECASE):
            try:
                cols, rows = _q(sql_usuario)
                if not rows:
                    return '<p>La consulta no devolvio resultados.</p>'
                return '<p><strong>Resultado de tu consulta SQL:</strong></p>' + _tabla(cols, rows)
            except Exception as e:
                return (
                    '<p style="color:var(--danger)"><strong>Error en tu SQL:</strong> %s</p>'
                    '<code style="display:block;padding:8px;background:#1a1a1a;border-radius:6px;'
                    'white-space:pre-wrap;font-size:12px;margin-top:8px">%s</code>' % (str(e), sql_usuario)
                )
        return '<p style="color:var(--danger)">Solo se permiten consultas <strong>SELECT</strong>.</p>'

    if intent == 'solo_lectura':
        return (
            '<div style="border-left:3px solid var(--warning,#f59e0b);padding:10px 14px;'
            'background:rgba(245,158,11,0.08);border-radius:6px">'
            '<p><strong>⚠️ Elipse es solo de consulta</strong></p>'
            '<p>No puedo <strong>borrar, crear, modificar ni eliminar</strong> datos del sistema. '
            'Hazlo desde el panel de administracion correspondiente.</p>'
            '</div>'
        )

    # ── RESUMEN ──────────────────────────────────────────────
    if intent == 'resumen':
        _, r1 = _q("SELECT COUNT(*) n FROM MAQUINA WHERE estado_maquina='OPERA'")
        _, r2 = _q("SELECT COUNT(*) n FROM MAQUINA WHERE estado_maquina='FALLO'")
        _, r3 = _q("SELECT COUNT(*) n FROM MAQUINA WHERE estado_maquina='MANTE'")
        _, r4 = _q("SELECT COUNT(*) n FROM REPORTE_FALLA WHERE estado_reporte IN ('ABIER','ENATE','ENESP')")
        _, r5 = _q("SELECT COUNT(*) n FROM ORDEN_MANTENIMIENTO WHERE estado_orden NOT IN ('CERRA','CANCE')")
        _, r6 = _q("SELECT COUNT(*) n FROM REFACCION WHERE stock <= stockMinimo")
        cards = _cards([
            {'label': 'Maquinas operativas',   'val': r1[0]['n'], 'sub': 'de la planta'},
            {'label': 'Maquinas en falla',     'val': r2[0]['n'], 'sub': 'requieren atencion'},
            {'label': 'En mantenimiento',      'val': r3[0]['n'], 'sub': 'ahora mismo'},
            {'label': 'Fallas abiertas',       'val': r4[0]['n'], 'sub': 'sin cerrar'},
            {'label': 'Ordenes activas',       'val': r5[0]['n'], 'sub': 'en proceso'},
            {'label': 'Refacciones bajo stock','val': r6[0]['n'], 'sub': 'reponer pronto'},
        ])
        return '<p><strong>📊 Resumen de OperaCore:</strong></p>%s' % cards

    # ── MAQUINAS ─────────────────────────────────────────────
    if intent == 'maquina_especifica':
        codigo = _extraer_codigo_maquina(pregunta)
        cols, rows = _q(
            "SELECT m.codigo Codigo, m.nombre Nombre, m.numeroSerie NumSerie,"
            " em.nombre Estado, l.nombre Linea, ma.nombre Marca, mo.nombre Modelo,"
            " m.fechaInstalacion Instalada"
            " FROM MAQUINA m"
            " LEFT JOIN EDO_MAQUINA em ON em.codigo = m.estado_maquina"
            " LEFT JOIN LINEA l ON l.codigo = m.linea"
            " LEFT JOIN MARCA ma ON ma.clave = m.marca"
            " LEFT JOIN MODELO mo ON mo.codigo = m.modelo"
            " WHERE m.codigo = %s", [codigo]
        )
        if not rows:
            return '<p>No encontre ninguna maquina con codigo <strong>%s</strong>.</p>' % codigo
        row = rows[0]
        cards = _cards([
            {'label': 'Maquina',  'val': row['Nombre'],  'sub': row['Codigo']},
            {'label': 'Estado',   'val': _badge(row['Estado']), 'sub': row['Linea'] or '-'},
            {'label': 'Marca/Modelo', 'val': '%s %s' % (row['Marca'] or '', row['Modelo'] or ''), 'sub': 'instalada %s' % row['Instalada']},
        ])
        _, ordenes = _q(
            "SELECT folio Folio, descripcion Descripcion, eo.nombre Estado, fechaProgramada Programada"
            " FROM ORDEN_MANTENIMIENTO o LEFT JOIN ESTADO_ORDEN eo ON eo.codigo = o.estado_orden"
            " WHERE o.maquina = %s ORDER BY o.fechaCreacion DESC LIMIT 5", [codigo]
        )
        extra = ('<p style="margin-top:10px"><strong>Ultimas ordenes:</strong></p>%s' % _tabla(
            ['Folio', 'Descripcion', 'Estado', 'Programada'], ordenes, est=['Estado'])) if ordenes else ''
        return '<p><strong>Maquina %s:</strong></p>%s%s' % (codigo, cards, extra)

    if intent in ('maquinas_en_falla', 'maquinas_en_mantenimiento', 'maquinas_operativas', 'maquinas_lista'):
        filtro = {
            'maquinas_en_falla': "WHERE m.estado_maquina = 'FALLO'",
            'maquinas_en_mantenimiento': "WHERE m.estado_maquina = 'MANTE'",
            'maquinas_operativas': "WHERE m.estado_maquina = 'OPERA'",
            'maquinas_lista': "",
        }[intent]
        cols, rows = _q(
            "SELECT m.codigo Codigo, m.nombre Nombre, em.nombre Estado, l.nombre Linea"
            " FROM MAQUINA m LEFT JOIN EDO_MAQUINA em ON em.codigo = m.estado_maquina"
            " LEFT JOIN LINEA l ON l.codigo = m.linea %s ORDER BY m.codigo" % filtro
        )
        titulo = {
            'maquinas_en_falla': 'Maquinas en falla',
            'maquinas_en_mantenimiento': 'Maquinas en mantenimiento',
            'maquinas_operativas': 'Maquinas operativas',
            'maquinas_lista': 'Todas las maquinas',
        }[intent]
        if not rows:
            return '<p>No hay maquinas en ese estado ahora mismo. 🎉</p>'
        return '<p><strong>%s:</strong></p>%s' % (titulo, _tabla(cols, rows, est=['Estado']))

    # ── INDICADORES ──────────────────────────────────────────
    if intent in ('indicadores_maquina', 'indicadores_general'):
        if intent == 'indicadores_maquina':
            codigo = _extraer_codigo_maquina(pregunta)
            cols, rows = _q(
                "SELECT m.codigo Codigo, m.nombre Nombre, i.mttr MTTR_horas, i.mtbf MTBF_horas,"
                " i.porcentajeDispo Disponibilidad, i.fechaInicio Desde, i.fechaFin Hasta"
                " FROM INDICADOR i JOIN MAQUINA m ON m.codigo = i.maquina"
                " WHERE i.maquina = %s ORDER BY i.fechaFin DESC LIMIT 5", [codigo]
            )
            if not rows:
                return '<p>No hay indicadores registrados para <strong>%s</strong>.</p>' % codigo
            return '<p><strong>Indicadores de %s:</strong></p>%s' % (codigo, _tabla(cols, rows))
        cols, rows = _q(
            "SELECT m.codigo Codigo, m.nombre Nombre, i.mttr MTTR_horas, i.mtbf MTBF_horas,"
            " i.porcentajeDispo Disponibilidad"
            " FROM INDICADOR i JOIN MAQUINA m ON m.codigo = i.maquina"
            " ORDER BY i.porcentajeDispo ASC LIMIT 20"
        )
        return '<p><strong>Indicadores por maquina (menor disponibilidad primero):</strong></p>%s' % _tabla(cols, rows)

    # ── FALLAS ───────────────────────────────────────────────
    if intent == 'falla_especifica':
        num = _extraer_numero_reporte(pregunta)
        cols, rows = _q(
            "SELECT r.numeroRegistro Reporte, r.asunto Asunto, r.descripcion Descripcion,"
            " r.causaRaiz CausaRaiz, r.fechaCreacion Creado, r.tiempoParo TiempoParoHrs,"
            " sev.nombre Severidad, er.nombre Estado, m.nombre Maquina,"
            " CONCAT(t.nombre,' ',t.apellidoPat) Reportado_por"
            " FROM REPORTE_FALLA r"
            " LEFT JOIN TIPO_SEVERIDAD sev ON sev.codigo = r.tipo_severidad"
            " LEFT JOIN EDO_REPORTE er ON er.codigo = r.estado_reporte"
            " LEFT JOIN MAQUINA m ON m.codigo = r.maquina"
            " LEFT JOIN TRABAJADOR t ON t.numeroNomina = r.trabajador"
            " WHERE r.numeroRegistro = %s", [num]
        )
        if not rows:
            return '<p>No encontre el reporte de falla #%s.</p>' % num
        row = rows[0]
        cards = _cards([
            {'label': 'Reporte', 'val': '#%s' % row['Reporte'], 'sub': row['Asunto']},
            {'label': 'Severidad', 'val': _badge(row['Severidad']), 'sub': row['Maquina']},
            {'label': 'Estado', 'val': _badge(row['Estado']), 'sub': row['Reportado_por'] or '-'},
        ])
        return '<p><strong>Reporte de falla #%s:</strong></p>%s%s' % (
            num, cards, _tabla(['Descripcion', 'CausaRaiz', 'Creado', 'TiempoParoHrs'], rows))

    if intent in ('fallas_criticas', 'fallas_abiertas', 'fallas_recientes'):
        filtro = {
            'fallas_criticas': "WHERE r.tipo_severidad = 'CRITI'",
            'fallas_abiertas': "WHERE r.estado_reporte IN ('ABIER','ENATE','ENESP')",
            'fallas_recientes': "",
        }[intent]
        orden = 'ORDER BY r.fechaCreacion DESC' if intent == 'fallas_recientes' else 'ORDER BY r.fechaCreacion DESC'
        cols, rows = _q(
            "SELECT r.numeroRegistro Reporte, r.asunto Asunto, m.nombre Maquina,"
            " sev.nombre Severidad, er.nombre Estado, r.fechaCreacion Creado"
            " FROM REPORTE_FALLA r"
            " LEFT JOIN MAQUINA m ON m.codigo = r.maquina"
            " LEFT JOIN TIPO_SEVERIDAD sev ON sev.codigo = r.tipo_severidad"
            " LEFT JOIN EDO_REPORTE er ON er.codigo = r.estado_reporte"
            " %s %s LIMIT 20" % (filtro, orden)
        )
        titulo = {'fallas_criticas': 'Fallas criticas', 'fallas_abiertas': 'Fallas abiertas', 'fallas_recientes': 'Fallas recientes'}[intent]
        if not rows:
            return '<p>No hay fallas en esa categoria ahora mismo. 🎉</p>'
        return '<p><strong>%s:</strong></p>%s' % (titulo, _tabla(cols, rows, est=['Severidad', 'Estado']))

    if intent == 'top_maquinas_fallas':
        n = _extraer_top_n(q) or 5
        cols, rows = _q(
            "SELECT m.codigo Codigo, m.nombre Nombre, COUNT(r.numeroRegistro) TotalFallas"
            " FROM MAQUINA m JOIN REPORTE_FALLA r ON r.maquina = m.codigo"
            " GROUP BY m.codigo, m.nombre ORDER BY TotalFallas DESC LIMIT %s", [n]
        )
        return '<p><strong>Top %d maquinas con mas fallas:</strong></p>%s' % (n, _tabla(cols, rows))

    # ── ORDENES ──────────────────────────────────────────────
    if intent == 'orden_especifica':
        folio = _extraer_folio_orden(pregunta)
        cols, rows = _q(
            "SELECT o.folio Folio, o.descripcion Descripcion, o.diagnostico Diagnostico,"
            " eo.nombre Estado, tm.nombre Tipo, m.nombre Maquina,"
            " CONCAT(t.nombre,' ',t.apellidoPat) Tecnico,"
            " o.fechaProgramada Programada, o.fechaCierre Cierre, o.porcentaje Avance"
            " FROM ORDEN_MANTENIMIENTO o"
            " LEFT JOIN ESTADO_ORDEN eo ON eo.codigo = o.estado_orden"
            " LEFT JOIN TIPO_MANTENIMIENTO tm ON tm.codigo = o.tipo_mantenimiento"
            " LEFT JOIN MAQUINA m ON m.codigo = o.maquina"
            " LEFT JOIN TRABAJADOR t ON t.numeroNomina = o.trabajador"
            " WHERE o.folio = %s", [folio]
        )
        if not rows:
            return '<p>No encontre la orden <strong>%s</strong>.</p>' % folio
        row = rows[0]
        cards = _cards([
            {'label': 'Orden', 'val': row['Folio'], 'sub': row['Tipo'] or '-'},
            {'label': 'Estado', 'val': _badge(row['Estado']), 'sub': '%s%% avance' % (row['Avance'] or 0)},
            {'label': 'Maquina', 'val': row['Maquina'] or '-', 'sub': row['Tecnico'] or 'sin asignar'},
        ])
        return '<p><strong>Orden %s:</strong></p>%s%s' % (
            folio, cards, _tabla(['Descripcion', 'Diagnostico', 'Programada', 'Cierre'], rows))

    if intent in ('ordenes_pendientes', 'ordenes_cerradas', 'ordenes_vencidas'):
        if intent == 'ordenes_pendientes':
            filtro = "WHERE o.estado_orden NOT IN ('CERRA','CANCE')"
        elif intent == 'ordenes_cerradas':
            filtro = "WHERE o.estado_orden = 'CERRA'"
        else:
            filtro = "WHERE o.fechaProgramada < CURDATE() AND o.estado_orden NOT IN ('CERRA','CANCE')"
        cols, rows = _q(
            "SELECT o.folio Folio, o.descripcion Descripcion, m.nombre Maquina,"
            " eo.nombre Estado, o.fechaProgramada Programada, o.porcentaje Avance"
            " FROM ORDEN_MANTENIMIENTO o"
            " LEFT JOIN MAQUINA m ON m.codigo = o.maquina"
            " LEFT JOIN ESTADO_ORDEN eo ON eo.codigo = o.estado_orden"
            " %s ORDER BY o.fechaProgramada ASC LIMIT 30" % filtro
        )
        titulo = {'ordenes_pendientes': 'Ordenes pendientes', 'ordenes_cerradas': 'Ordenes cerradas', 'ordenes_vencidas': 'Ordenes vencidas'}[intent]
        if not rows:
            msg = '¡Ninguna orden vencida, todo al dia! 🎉' if intent == 'ordenes_vencidas' else 'No hay ordenes en esa categoria.'
            return '<p>%s</p>' % msg
        return '<p><strong>%s:</strong></p>%s' % (titulo, _tabla(cols, rows, est=['Estado']))

    if intent == 'top_tecnicos':
        n = _extraer_top_n(q) or 5
        cols, rows = _q(
            "SELECT CONCAT(t.nombre,' ',t.apellidoPat) Tecnico, COUNT(o.folio) OrdenesCerradas"
            " FROM TRABAJADOR t JOIN ORDEN_MANTENIMIENTO o ON o.trabajador = t.numeroNomina"
            " WHERE o.estado_orden = 'CERRA'"
            " GROUP BY t.numeroNomina, Tecnico ORDER BY OrdenesCerradas DESC LIMIT %s", [n]
        )
        return '<p><strong>Top %d tecnicos por ordenes cerradas:</strong></p>%s' % (n, _tabla(cols, rows))

    if intent == 'ordenes_de_tecnico':
        nombre = _extraer_nombre_propio(pregunta, 'tecnico|trabajador') or _extraer_nombre_propio(pregunta, 'de')
        if not nombre:
            return '<p>Dime el nombre, ej: <em>"ordenes del tecnico Juan Perez"</em></p>'
        cols, rows = _q(
            "SELECT o.folio Folio, o.descripcion Descripcion, eo.nombre Estado, o.fechaProgramada Programada"
            " FROM ORDEN_MANTENIMIENTO o"
            " JOIN TRABAJADOR t ON t.numeroNomina = o.trabajador"
            " LEFT JOIN ESTADO_ORDEN eo ON eo.codigo = o.estado_orden"
            " WHERE LOWER(CONCAT(t.nombre,' ',t.apellidoPat,' ',COALESCE(t.apellidoMat,''))) LIKE LOWER(%s)"
            " ORDER BY o.fechaCreacion DESC LIMIT 20", ['%' + nombre + '%']
        )
        if not rows:
            return '<p>No encontre ordenes para <strong>%s</strong>.</p>' % nombre
        return '<p><strong>Ordenes de %s:</strong></p>%s' % (nombre, _tabla(cols, rows, est=['Estado']))

    # ── INVENTARIO ───────────────────────────────────────────
    if intent == 'refacciones_bajo_stock':
        cols, rows = _q(
            "SELECT r.nombre Refaccion, r.codigoSku SKU, r.stock Stock, r.stockMinimo Minimo,"
            " cl.nombre Criticidad"
            " FROM REFACCION r LEFT JOIN CLASIFICACION cl ON cl.codigo = r.clasificacion"
            " WHERE r.stock <= r.stockMinimo ORDER BY (r.stockMinimo - r.stock) DESC"
        )
        if not rows:
            return '<p>Todas las refacciones tienen stock suficiente. 🎉</p>'
        return '<p><strong>⚠️ Refacciones con bajo stock:</strong></p>%s' % _tabla(cols, rows)

    if intent == 'refaccion_buscar':
        m = re.search(r'refaccion(?:es)?\s+([a-záéíóúñ0-9 ]{3,})', pregunta.lower())
        nombre = m.group(1).strip() if m else None
        if not nombre:
            return '<p>Dime el nombre, ej: <em>"busca la refaccion rodamiento"</em></p>'
        cols, rows = _q(
            "SELECT r.nombre Refaccion, r.codigoSku SKU, r.stock Stock, r.stockMinimo Minimo, r.costo Costo"
            " FROM REFACCION r WHERE LOWER(r.nombre) LIKE LOWER(%s) LIMIT 20", ['%' + nombre + '%']
        )
        if not rows:
            return '<p>No encontre refacciones con "%s".</p>' % nombre
        return '<p><strong>Resultados para "%s":</strong></p>%s' % (nombre, _tabla(cols, rows, dinero=['Costo']))

    if intent == 'herramientas_disponibles':
        cols, rows = _q(
            "SELECT h.nombre Herramienta, th.nombre Tipo, eh.cantidad Cantidad"
            " FROM ESTADO_HERRAMIENTA eh"
            " JOIN HERRAMIENTA h ON h.numeroRegistro = eh.herramienta"
            " JOIN TIPO_HERRAMIENTA th ON th.numeroRegistro = h.tipo_herramienta"
            " WHERE eh.edo_herramienta = 'DISPO' AND eh.cantidad > 0"
        )
        if not rows:
            return '<p>No hay herramientas disponibles ahora mismo.</p>'
        return '<p><strong>🔧 Herramientas disponibles:</strong></p>%s' % _tabla(cols, rows)

    # ── TRABAJADORES ─────────────────────────────────────────
    if intent == 'trabajadores_lista':
        cols, rows = _q(
            "SELECT t.numeroNomina Nomina, CONCAT(t.nombre,' ',t.apellidoPat) Nombre,"
            " ro.nombre Rol, CASE WHEN t.actividad=1 THEN 'Activo' ELSE 'Inactivo' END Estado"
            " FROM TRABAJADOR t LEFT JOIN ROL ro ON ro.codigo = t.rol"
            " WHERE t.actividad = 1 ORDER BY t.apellidoPat LIMIT 50"
        )
        return '<p><strong>Trabajadores activos:</strong></p>%s' % _tabla(cols, rows)

    if intent == 'trabajadores_por_rol':
        cols, rows = _q(
            "SELECT ro.nombre Rol, COUNT(*) Total FROM TRABAJADOR t"
            " LEFT JOIN ROL ro ON ro.codigo = t.rol GROUP BY ro.nombre ORDER BY Total DESC"
        )
        return '<p><strong>Trabajadores por rol:</strong></p>%s' % _tabla(cols, rows)

    if intent == 'trabajador_buscar':
        m = re.search(r'trabajador(?:a)?\s+([a-záéíóúñ ]{3,})|tecnico\s+([a-záéíóúñ ]{3,})', pregunta.lower())
        nombre = (m.group(1) or m.group(2)).strip() if m else None
        if not nombre:
            return '<p>Dime el nombre, ej: <em>"busca al trabajador Juan Perez"</em></p>'
        cols, rows = _q(
            "SELECT t.numeroNomina Nomina, CONCAT(t.nombre,' ',t.apellidoPat,' ',COALESCE(t.apellidoMat,'')) Nombre,"
            " ro.nombre Rol, esp.nombre Especialidad,"
            " CASE WHEN t.actividad=1 THEN 'Activo' ELSE 'Inactivo' END Estado"
            " FROM TRABAJADOR t"
            " LEFT JOIN ROL ro ON ro.codigo = t.rol"
            " LEFT JOIN ESPECIALIDAD esp ON esp.numeroRegistro = t.especialidad"
            " WHERE LOWER(CONCAT(t.nombre,' ',t.apellidoPat,' ',COALESCE(t.apellidoMat,''))) LIKE LOWER(%s)"
            " LIMIT 20", ['%' + nombre + '%']
        )
        if not rows:
            return '<p>No encontre trabajadores con "%s".</p>' % nombre
        return '<p><strong>Resultados para "%s":</strong></p>%s' % (nombre, _tabla(cols, rows))

    return None  # → cae a la IA


# ─────────────────────────────────────────────────────────
# Llamada a Groq
# ─────────────────────────────────────────────────────────

def _llamar_groq(system, user_msg, modelo_id, historial=None, max_tokens=600, temperature=0.2):
    api_key = settings.GROQ_API_KEY
    if not api_key:
        return None, 'No hay API key de Groq configurada (revisa GROQ_API_KEY en el .env del api).'

    messages = [{'role': 'system', 'content': system}]
    for m in (historial or [])[-6:]:
        if m.get('role') in ('user', 'assistant') and m.get('content'):
            messages.append({'role': m['role'], 'content': str(m['content'])[:1200]})
    messages.append({'role': 'user', 'content': user_msg})

    payload = json.dumps({
        'model': modelo_id,
        'max_tokens': max_tokens,
        'temperature': temperature,
        'messages': messages,
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.groq.com/openai/v1/chat/completions',
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + api_key,
            'User-Agent': 'Mozilla/5.0 (compatible; OperaCore-Elipse/2.0)',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            data = json.loads(res.read().decode('utf-8'))
            return data['choices'][0]['message']['content'].strip(), None
    except urllib.error.HTTPError as e:
        return None, 'Error Groq %s: %s' % (e.code, e.read().decode('utf-8', errors='ignore')[:200])
    except Exception as e:
        return None, 'Error: %s' % str(e)


# ─────────────────────────────────────────────────────────
# Modo IA con SQL dinamico (fallback)
# ─────────────────────────────────────────────────────────

def _ai_con_sql(pregunta, modelo_key, historial=None):
    modelo_id = MODELOS_IA.get(modelo_key, MODELOS_IA[MODELO_DEFAULT])['id']

    sql_raw, err = _llamar_groq(SQL_SYSTEM_PROMPT, pregunta, modelo_id, historial=historial, max_tokens=400, temperature=0.0)
    if err:
        if _es_error_conexion(err):
            return _respuesta_sin_internet(pregunta)
        return '<p class="msg-error">%s</p>' % err

    sql_raw = sql_raw.strip()
    sql_raw = re.sub(r'^```sql\s*', '', sql_raw, flags=re.IGNORECASE)
    sql_raw = re.sub(r'^```\s*', '', sql_raw)
    sql_raw = re.sub(r'```$', '', sql_raw).strip()

    if sql_raw.upper().startswith('NO_SQL') or not sql_raw.upper().startswith('SELECT'):
        resp, err2 = _llamar_groq(SYSTEM_PROMPT, pregunta, modelo_id, historial=historial, max_tokens=600, temperature=0.3)
        if err2:
            if _es_error_conexion(err2):
                return _respuesta_sin_internet(pregunta)
            return '<p class="msg-error">%s</p>' % err2
        return _texto_a_html(resp)

    try:
        cols, rows = _q(sql_raw)
    except Exception as e:
        return (
            '<details style="margin-bottom:8px;font-size:11px;color:var(--color-muted,#94a3b8)">'
            '<summary>SQL generado (con error)</summary>'
            '<code style="display:block;padding:6px;background:#1a1a1a;border-radius:6px;'
            'white-space:pre-wrap;color:#fff">%s</code>'
            '<p style="color:var(--danger)">Error: %s</p>'
            '</details>' % (sql_raw, str(e))
        )

    SYSTEM_ADMIN = (
        SYSTEM_PROMPT +
        "\n\nIMPORTANTE: Eres asistente del PANEL INTERNO de OperaCore. "
        "NUNCA digas 'no tengo acceso'. Los datos ya estan disponibles. Respondelos directamente."
    )

    if not rows:
        interpretacion, _ = _llamar_groq(
            SYSTEM_ADMIN,
            'El usuario pregunto: "%s"\nNo encontre ningun resultado. Responde en UNA oracion corta.' % pregunta,
            modelo_id, historial=historial, max_tokens=120, temperature=0.1
        )
        tabla_html = '<em>Sin resultados en la base de datos.</em>'
    else:
        muestra = rows[:20]
        datos_str = json.dumps(muestra, ensure_ascii=False, default=str)
        total_str = ' (%d registros en total)' % len(rows) if len(rows) > 20 else ' (%d registros)' % len(rows)
        interpretacion, _ = _llamar_groq(
            SYSTEM_ADMIN,
            'El usuario pregunto: "%s"\nDatos reales%s:\n%s\n\n'
            'Responde DIRECTAMENTE usando estos datos. Menciona valores exactos. '
            'No digas que no tienes acceso. No menciones JSON.' % (pregunta, total_str, datos_str),
            modelo_id, historial=historial, max_tokens=500, temperature=0.2
        )
        tabla_html = _tabla(cols, rows)

    partes = []
    if interpretacion:
        partes.append(_texto_a_html(interpretacion))
    if rows:
        partes.append(
            '<details style="margin-top:10px">'
            '<summary style="cursor:pointer;font-size:12px;color:var(--color-muted,#94a3b8)">'
            'Ver tabla completa (%d filas)</summary>%s</details>' % (len(rows), tabla_html)
        )
    return ''.join(partes) if partes else tabla_html


# ─────────────────────────────────────────────────────────
# Vista principal
# ─────────────────────────────────────────────────────────

class ElipseChatAPIView(APIView):
    def post(self, request):
        pregunta = (request.data.get('pregunta') or '').strip()
        modelo_k = request.data.get('modelo', MODELO_DEFAULT)
        historial = request.data.get('historial', [])

        if not pregunta:
            return Response({'error': 'Escribe una pregunta.'})
        if modelo_k not in MODELOS_IA:
            modelo_k = MODELO_DEFAULT

        intent = _intent(pregunta)
        try:
            html = _resolve(intent, pregunta)
        except Exception as e:
            html = '<p class="msg-error">Error consultando la base de datos: %s</p>' % str(e)

        if html is None:
            html = _ai_con_sql(pregunta, modelo_k, historial=historial)

        return Response({'html': html, 'intent': intent, 'modelo': MODELOS_IA[modelo_k]['label']})