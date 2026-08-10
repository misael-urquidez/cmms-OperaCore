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
import base64
import difflib
import json
import re
import unicodedata
import urllib.request
import urllib.error
from datetime import date
from html import escape, unescape
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

from django.conf import settings
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response


_PLANTILLA_CAMPOS = [
    # (campo, patron de la etiqueta -- debe ocupar TODO el renglon, texto
    #  de ejemplo/cursiva de la plantilla que hay que ignorar si aparece)
    ('asunto', r'^\s*asunto\s*:?\s*$',
     'resume la falla en una frase corta.'),
    ('descripcion', r'^\s*descripcion\s*:?\s*$',
     'que paso? explica la falla con el mayor detalle posible.'),
    ('causaRaiz', r'^\s*causa\s+raiz\s*:?\s*$',
     'por que crees que paso? (si aun no lo sabes, dejalo en blanco)'),
    ('tiempoParo', r'^\s*tiempo\s+que\s+estuvo\s+en\s+paro\s+la\s+maquina\s*(?:\(horas\))?\s*:?\s*$',
     'ej. 2.5'),
    ('fecha', r'^\s*fecha\s+de\s+solucion\s*:?\s*$',
     'formato dd/mm/aaaa, si ya se resolvio.'),
    ('maquina', r'^\s*maquina\s*:?\s*$',
     'nombre o codigo de la maquina afectada.'),
    ('tipo_severidad', r'^\s*severidad\s*:?\s*$',
     'baja, media, alta o critica.'),
    ('tipo_falla', r'^\s*tipo\(?s?\)?\s+de\s+falla\s*:?\s*$',
     'ej. electrica, mecanica, software...'),
]


def _quitar_acentos(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))


def _extraer_por_plantilla(texto):
    """Si el documento sigue 'plantilla_reporte_falla.docx' (o algo muy
    parecido), usa sus etiquetas como anclas para cortar el texto en
    secciones EXACTAS, en vez de adivinar con heuristicas genericas sobre
    todo el documento junto. Regresa un dict {campo: texto_de_esa_seccion}
    o None si no reconoce suficientes etiquetas como para confiar en esto."""
    plano = _quitar_acentos(texto).lower()

    matches = []
    for campo, patron, _pista in _PLANTILLA_CAMPOS:
        m = re.search(patron, plano, re.MULTILINE)
        if m:
            matches.append((campo, m.start(), m.end()))

    if len(matches) < 3:
        return None  # no parece la plantilla, mejor el modo generico

    matches.sort(key=lambda t: t[1])
    pistas = {campo: pista for campo, _p, pista in _PLANTILLA_CAMPOS}

    secciones = {}
    for i, (campo, _ini, fin) in enumerate(matches):
        fin_seccion = matches[i + 1][1] if i + 1 < len(matches) else len(texto)
        crudo = texto[fin:fin_seccion].strip()

        # quita el texto de ejemplo/cursiva de la plantilla si el tecnico
        # lo dejo intacto (evita confundir "media" del ejemplo de
        # severidad con una respuesta real, por ejemplo)
        crudo_plano = _quitar_acentos(crudo).lower()
        pista = pistas.get(campo, '')
        if pista and crudo_plano.startswith(pista):
            crudo = crudo[len(pista):].strip()

        secciones[campo] = crudo

    return secciones


def _autofill_local(texto, maquinas, severidades, tipos_falla, estados):
    """Extraccion basica SIN IA, para cuando Elipse no tiene conexion/API
    key. Primero intenta reconocer la plantilla oficial (etiquetas fijas,
    mucho mas confiable); si el documento no la sigue, cae a heuristicas
    genericas sobre texto libre. En ambos casos es menos precisa que el
    modelo, asi que siempre avisa que campos no pudo identificar."""
    campos = {
        'asunto': None, 'descripcion': None, 'causaRaiz': None,
        'tiempoParo': None, 'fecha': None, 'maquina': None,
        'tipo_severidad': None, 'tipo_falla': None, 'estado_reporte': None,
    }
    avisos = []

    secciones = _extraer_por_plantilla(texto)
    usando_plantilla = secciones is not None

    if usando_plantilla:
        campos['asunto'] = (secciones.get('asunto') or '')[:80] or None
        campos['descripcion'] = (secciones.get('descripcion') or '')[:500] or None
        campos['causaRaiz'] = (secciones.get('causaRaiz') or '')[:500] or None
        texto_maquina = secciones.get('maquina') or ''
        texto_severidad = secciones.get('tipo_severidad') or ''
        texto_falla = secciones.get('tipo_falla') or ''
        texto_tiempo = secciones.get('tiempoParo') or ''
        texto_fecha = secciones.get('fecha') or ''
    else:
        texto_low_completo = (texto or '').lower()
        primera_linea = next((l.strip() for l in texto.splitlines() if l.strip()), '')
        campos['asunto'] = primera_linea[:80] or None
        campos['descripcion'] = texto.strip()[:500] or None
        texto_maquina = texto_severidad = texto_falla = texto_low_completo
        texto_tiempo = texto_low_completo
        texto_fecha = texto

    # tiempo de paro: "N horas"/"N hrs" en cualquier modo; si viene de la
    # plantilla tambien acepta solo el numero solo (la seccion ya viene
    # aislada, ej. "2.5")
    m = re.search(r'(\d+(?:\.\d+)?)\s*(?:horas?|hrs?)\b', texto_tiempo.lower())
    if not m and usando_plantilla:
        m = re.match(r'\s*(\d+(?:\.\d+)?)\s*$', texto_tiempo.strip())
    if m:
        try:
            campos['tiempoParo'] = float(m.group(1))
        except ValueError:
            pass

    # fecha: dd/mm/aaaa -> YYYY-MM-DD (solo tiene sentido buscarla si vino
    # de la seccion "Fecha de solucion" de la plantilla)
    if usando_plantilla:
        m = re.search(r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})', texto_fecha)
        if m:
            dd, mm, yyyy = m.groups()
            try:
                campos['fecha'] = date(int(yyyy), int(mm), int(dd)).isoformat()
            except ValueError:
                pass

    # maquina: coincidencia exacta de codigo/nombre, si no hay -> similitud
    maquina_low = texto_maquina.lower()
    mejor_maquina, mejor_score = None, 0.0
    for maq in (maquinas or []):
        nombre = (maq.get('nombre') or '').lower()
        codigo = (maq.get('codigo') or '').lower()
        if (codigo and codigo in maquina_low) or (nombre and nombre in maquina_low):
            mejor_maquina, mejor_score = maq.get('codigo'), 1.0
            break
        score = difflib.SequenceMatcher(None, nombre, maquina_low).ratio() if nombre else 0.0
        if score > mejor_score:
            mejor_maquina, mejor_score = maq.get('codigo'), score
    # con plantilla la seccion ya viene aislada (solo el nombre de la
    # maquina), asi que un umbral mas bajo sigue siendo confiable
    umbral = 0.35 if usando_plantilla else 0.5
    if mejor_maquina and mejor_score >= umbral:
        campos['maquina'] = mejor_maquina
    else:
        avisos.append('la maquina')

    # severidad: palabras clave -> codigo (solo si ese codigo existe en catalogo)
    severidad_low = texto_severidad.lower()
    mapa_severidad = [
        (('critic', 'parada total', 'linea parada', 'urgente'), 'CRITI'),
        (('alta', 'grave'), 'ALTA'),
        (('media', 'moderad'), 'MEDI'),
        (('baja', 'menor', 'leve'), 'BAJA'),
    ]
    codigos_severidad = {s.get('codigo') for s in (severidades or [])}
    for claves, codigo in mapa_severidad:
        if codigo in codigos_severidad and any(k in severidad_low for k in claves):
            campos['tipo_severidad'] = codigo
            break
    if not campos['tipo_severidad']:
        avisos.append('la severidad')

    # tipo de falla: coincidencia de nombre dentro de su seccion
    falla_low = texto_falla.lower()
    for tf in (tipos_falla or []):
        nombre = (tf.get('nombre') or '').lower()
        if nombre and nombre in falla_low:
            campos['tipo_falla'] = tf.get('numeroRegistro')
            break

    # estado: default a ABIER si existe en el catalogo (igual que en modo IA)
    codigos_estado = {e.get('codigo') for e in (estados or [])}
    if 'ABIER' in codigos_estado:
        campos['estado_reporte'] = 'ABIER'

    base = (
        'Elipse no tiene conexion a la IA ahorita, asi que use una extraccion '
        + ('basica siguiendo la plantilla' if usando_plantilla else 'basica del texto')
        + ' (sin IA, menos precisa de lo normal).'
    )
    if avisos:
        mensaje = base + ' No logre identificar %s: revisalo y complementalo a mano antes de guardar.' % ' ni '.join(avisos)
    else:
        mensaje = base + ' Revisa todos los campos antes de guardar.'

    return campos, mensaje


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


def _esc(val):
    """Escapa un valor que viene de la BD antes de meterlo en el HTML.

    Los textos libres (descripcion de una falla, notas de una orden) los
    escribe el usuario desde el panel, asi que pueden traer < > & sin mala
    intencion -- o con ella. Todo lo que sale de _q() pasa por aqui."""
    return escape(str(val), quote=False)


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
    return '<span class="badge %s">&#9679; %s</span>' % (cls, _esc(val))

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
    th = ''.join('<th>%s</th>' % _esc(c) for c in cols)
    trs = []
    for row in vis:
        tds = []
        for c in cols:
            v = row.get(c)
            if c in est:
                tds.append('<td>%s</td>' % _badge(v))
            elif c in dinero:
                tds.append('<td>%s</td>' % _esc(_dinero(v)))
            elif v is None:
                tds.append('<td>-</td>')
            else:
                tds.append('<td>%s</td>' % _esc(v))
        trs.append('<tr>%s</tr>' % ''.join(tds))
    nota = ('<p style="margin-top:6px;font-size:11px;color:var(--color-muted,#94a3b8)">... y %d filas mas.</p>' % extra) if extra else ''
    return '<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>%s' % (th, ''.join(trs), nota)

def _cards(items):
    """Tarjetas de resumen. 'label' y 'sub' se escapan siempre; 'val' se
    inserta tal cual porque a veces ya es HTML (un _badge). Quien llame con
    un valor de la BD en 'val' debe pasarlo por _esc()."""
    parts = []
    for i in items:
        parts.append(
            '<div class="stat-card">'
            '<div class="s-label">%s</div>'
            '<div class="s-val">%s</div>'
            '<div class="s-sub">%s</div>'
            '</div>' % (_esc(i['label']), i['val'], _esc(i.get('sub', '')))
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

def _catalogo_texto(items, campos):
    """Formatea una lista de dicts en lineas 'valor | valor' para meter en un
    prompt (catalogo de maquinas/severidades/tipos de falla que Elipse puede
    usar para el autocompletado del reporte de falla)."""
    out = []
    for it in (items or [])[:200]:
        if not isinstance(it, dict):
            continue
        out.append(' | '.join(str(it.get(c, '')) for c in campos))
    return '\n'.join(out) if out else '(sin datos disponibles)'


ETIQUETAS_CAMPO_FALLA = {
    'asunto': 'Asunto', 'descripcion': 'Descripcion', 'causaRaiz': 'Causa raiz',
    'tiempoParo': 'Tiempo de paro (hrs)', 'fecha': 'Fecha', 'maquina': 'Maquina',
    'tipo_severidad': 'Severidad', 'tipo_falla': 'Tipo de falla',
    'estado_reporte': 'Estado del reporte',
}


def _nombre_por_codigo(catalogo, valor):
    """Busca en un catalogo [{'codigo':..,'nombre':..}, ...] el nombre legible
    de un codigo ya confirmado, para mostrarselo al modelo en texto plano en
    vez del codigo crudo."""
    for it in (catalogo or []):
        if not isinstance(it, dict):
            continue
        clave = it.get('codigo', it.get('numeroRegistro'))
        if str(clave) == str(valor):
            return it.get('nombre', str(valor))
    return str(valor)


def _texto_campos_confirmados(campos_previos, maquinas=None, severidades=None,
                               tipos_falla=None, estados=None):
    """Arma el bloque 'CAMPOS YA CONFIRMADOS' que se inyecta en el system
    prompt para que el modelo deje de volver a preguntar por datos que el
    tecnico ya dio en un turno anterior (en vez de confiar en que lo
    detecte solo, revolviendo el historial de chat)."""
    if not campos_previos:
        return '(ninguno todavia, es el primer turno)'
    catalogos = {
        'maquina': maquinas, 'tipo_severidad': severidades,
        'tipo_falla': tipos_falla, 'estado_reporte': estados,
    }
    lineas = []
    for k, v in campos_previos.items():
        if v in (None, ''):
            continue
        etiqueta = ETIQUETAS_CAMPO_FALLA.get(k, k)
        cat = catalogos.get(k)
        legible = _nombre_por_codigo(cat, v) if cat else v
        lineas.append('- %s: %s' % (etiqueta, legible))
    return '\n'.join(lineas) if lineas else '(ninguno todavia, es el primer turno)'


def _parsear_json_autofill(crudo, claves=(
        'asunto', 'descripcion', 'causaRaiz', 'tiempoParo', 'fecha',
        'maquina', 'tipo_severidad', 'tipo_falla', 'estado_reporte')):
    """El modelo deberia regresar JSON puro, pero a veces lo envuelve en
    ```json ... ``` pese a la instruccion, o le mete texto alrededor. Este
    parser es tolerante a eso; regresa (campos, mensaje), o (None, None) si
    no logra sacar un dict. `claves` son los campos esperados ademas de
    "mensaje" -- por default los del reporte de falla, pero se puede pasar
    otro juego (p.ej. los de "crear orden de mantenimiento")."""
    if not crudo:
        return None, None
    s = crudo.strip()
    if s.startswith('```'):
        s = re.sub(r'^```[a-zA-Z]*\n?', '', s)
        s = re.sub(r'```\s*$', '', s).strip()
    data = None
    try:
        data = json.loads(s)
    except ValueError:
        m = re.search(r'\{.*\}', s, re.S)
        if m:
            try:
                data = json.loads(m.group(0))
            except ValueError:
                data = None
    if not isinstance(data, dict):
        return None, None

    mensaje = data.get('mensaje') or None
    campos = {k: data.get(k) for k in claves}
    return campos, mensaje


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

    # Levantar un reporte de falla guiado. Va ANTES del candado de escritura
    # porque comparte verbos con el ("registra", "crea"): aqui no escribimos
    # en la BD, solo proponemos los campos del formulario para que el tecnico
    # los revise y mande el mismo.
    if has('reporta', 'reportar', 'levanta', 'levantar', 'registra', 'registrar',
           'abre', 'crea') and has('falla', 'reporte de falla'):
        return 'crear_reporte_falla'

    # Levantar una orden de mantenimiento guiada. Mismo criterio que arriba:
    # va antes del candado de escritura porque comparte verbos con el
    # ("crea", "programa", "registra"), pero aqui tampoco se escribe en la
    # BD -- solo se proponen los campos para que el tecnico/admin los revise
    # y de "Crear" el mismo desde el formulario normal.
    if has('crea', 'crear', 'programa', 'programar', 'levanta', 'levantar',
           'registra', 'registrar', 'abre', 'genera') and has('orden'):
        return 'crear_orden_mantenimiento'

    # Intento de modificar BD. Palabra completa, no substring: "registra" no
    # debe hacer match dentro de "maquinas registradas", que es solo consulta.
    for palabra in PALABRAS_MODIFICAR:
        if re.search(r'\b' + re.escape(palabra) + r'\b', q):
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
# ── Busqueda externa en internet (SOLO si tiene que ver con maquinaria/CMMS,
    #    nunca por preguntas genericas tipo "puedes buscar en internet?") ────
    tema_maquinaria = has(
        'maquina', 'maquinas', 'maq', 'equipo', 'equipos', 'marca', 'modelo',
        'refaccion', 'refacciones', 'pieza', 'piezas', 'componente', 'sensor',
        'falla', 'fallas', 'averia', 'reparacion',
    ) or _extraer_codigo_maquina(q_orig) is not None

    pide_info_tecnica = has(
        'especificacion', 'especificaciones', 'ficha tecnica', 'hoja de datos',
        'datasheet', 'manual del fabricante', 'manual de la maquina',
        'informacion de la marca', 'catalogo del fabricante',
    )
    pide_solucion = has(
        'como solucionar', 'como resolver', 'como reparar', 'como arreglar',
        'solucion a', 'solucion para', 'como se arregla', 'como se repara',
        'que hago con', 'que hago si',
    )
    pide_busqueda_explicita = has(
        'busca en internet', 'buscalo en internet', 'buscar en internet',
        'en internet', 'en google', 'busca en la web',
    )

    if pide_info_tecnica and tema_maquinaria:
        return 'buscar_web'
    if pide_solucion and tema_maquinaria:
        return 'buscar_web'
    if pide_busqueda_explicita and tema_maquinaria:
        return 'buscar_web'

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
                    'white-space:pre-wrap;font-size:12px;margin-top:8px">%s</code>' % (_esc(e), _esc(sql_usuario))
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
            return '<p>No encontre ninguna maquina con codigo <strong>%s</strong>.</p>' % _esc(codigo)
        row = rows[0]
        cards = _cards([
            {'label': 'Maquina',  'val': _esc(row['Nombre']),  'sub': row['Codigo']},
            {'label': 'Estado',   'val': _badge(row['Estado']), 'sub': row['Linea'] or '-'},
            {'label': 'Marca/Modelo', 'val': _esc('%s %s' % (row['Marca'] or '', row['Modelo'] or '')), 'sub': 'instalada %s' % row['Instalada']},
        ])
        _, ordenes = _q(
            "SELECT folio Folio, descripcion Descripcion, eo.nombre Estado, fechaProgramada Programada"
            " FROM ORDEN_MANTENIMIENTO o LEFT JOIN ESTADO_ORDEN eo ON eo.codigo = o.estado_orden"
            " WHERE o.maquina = %s ORDER BY o.fechaCreacion DESC LIMIT 5", [codigo]
        )
        extra = ('<p style="margin-top:10px"><strong>Ultimas ordenes:</strong></p>%s' % _tabla(
            ['Folio', 'Descripcion', 'Estado', 'Programada'], ordenes, est=['Estado'])) if ordenes else ''
        return '<p><strong>Maquina %s:</strong></p>%s%s' % (_esc(codigo), cards, extra)

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
                return '<p>No hay indicadores registrados para <strong>%s</strong>.</p>' % _esc(codigo)
            return '<p><strong>Indicadores de %s:</strong></p>%s' % (_esc(codigo), _tabla(cols, rows))
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
            return '<p>No encontre el reporte de falla #%s.</p>' % _esc(num)
        row = rows[0]
        cards = _cards([
            {'label': 'Reporte', 'val': '#%s' % _esc(row['Reporte']), 'sub': row['Asunto']},
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
            return '<p>No encontre la orden <strong>%s</strong>.</p>' % _esc(folio)
        row = rows[0]
        cards = _cards([
            {'label': 'Orden', 'val': _esc(row['Folio']), 'sub': row['Tipo'] or '-'},
            {'label': 'Estado', 'val': _badge(row['Estado']), 'sub': '%s%% avance' % (row['Avance'] or 0)},
            {'label': 'Maquina', 'val': _esc(row['Maquina'] or '-'), 'sub': row['Tecnico'] or 'sin asignar'},
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
            return '<p>No encontre ordenes para <strong>%s</strong>.</p>' % _esc(nombre)
        return '<p><strong>Ordenes de %s:</strong></p>%s' % (_esc(nombre), _tabla(cols, rows, est=['Estado']))

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
            return '<p>No encontre refacciones con "%s".</p>' % _esc(nombre)
        return '<p><strong>Resultados para "%s":</strong></p>%s' % (_esc(nombre), _tabla(cols, rows, dinero=['Costo']))

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
            return '<p>No encontre trabajadores con "%s".</p>' % _esc(nombre)
        return '<p><strong>Resultados para "%s":</strong></p>%s' % (_esc(nombre), _tabla(cols, rows))

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
        return '<p class="msg-error">%s</p>' % _esc(err)

    sql_raw = sql_raw.strip()
    sql_raw = re.sub(r'^```sql\s*', '', sql_raw, flags=re.IGNORECASE)
    sql_raw = re.sub(r'^```\s*', '', sql_raw)
    sql_raw = re.sub(r'```$', '', sql_raw).strip()

    if sql_raw.upper().startswith('NO_SQL') or not sql_raw.upper().startswith('SELECT'):
        resp, err2 = _llamar_groq(SYSTEM_PROMPT, pregunta, modelo_id, historial=historial, max_tokens=600, temperature=0.3)
        if err2:
            if _es_error_conexion(err2):
                return _respuesta_sin_internet(pregunta)
            return '<p class="msg-error">%s</p>' % _esc(err2)
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
            '</details>' % (_esc(sql_raw), _esc(e))
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
# Busqueda en internet (DuckDuckGo, sin API key)
# ─────────────────────────────────────────────────────────

def _limpiar_html_tags(s):
    return unescape(re.sub(r'<[^>]+>', '', s)).strip()


def _extraer_url_real(href):
    # DuckDuckGo envuelve los links salientes en una redireccion propia
    # (//duckduckgo.com/l/?uddg=<url-real-codificada>&...). Aqui la desenvolvemos.
    if 'duckduckgo.com/l/' in href:
        qs = parse_qs(urlparse(href).query)
        if 'uddg' in qs:
            return unquote(qs['uddg'][0])
    return href


def _buscar_web(query, max_resultados=5):
    """Scraping simple del HTML de DuckDuckGo (no requiere API key).
    Es fragil por naturaleza: si DuckDuckGo cambia su HTML esto puede dejar
    de funcionar. Si eso pasa, la funcion regresa (lista vacia, error) y
    _resolver_busqueda_web ya maneja ese caso avisando al usuario en vez
    de tronar."""
    url = 'https://html.duckduckgo.com/html/?q=' + quote_plus(query)
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            html_doc = res.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return [], str(e)

    patron = re.compile(
        r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>(.*?)</a>.*?'
        r'<a class="result__snippet"[^>]*>(.*?)</a>',
        re.DOTALL,
    )
    resultados = []
    for href, titulo_html, snippet_html in patron.findall(html_doc):
        titulo = _limpiar_html_tags(titulo_html)
        snippet = _limpiar_html_tags(snippet_html)
        link = _extraer_url_real(href)
        if titulo and link:
            resultados.append({'titulo': titulo, 'snippet': snippet, 'url': link})
        if len(resultados) >= max_resultados:
            break
    return resultados, None


def _resolver_busqueda_web(pregunta, modelo_key, historial=None):
    modelo_id = MODELOS_IA.get(modelo_key, MODELOS_IA[MODELO_DEFAULT])['id']

    # Si la pregunta trae el codigo interno de una maquina (MAQ003), sacamos
    # su marca/modelo real de la BD para buscar algo que internet si entienda.
    query_busqueda = pregunta
    contexto_maquina = ''
    codigo_maq = _extraer_codigo_maquina(pregunta)
    es_troubleshooting = any(p in pregunta.lower() for p in (
            'solucionar', 'reparar', 'arreglar', 'resolver', 'falla', 'problema', 'averia',
        ))

    if codigo_maq:
            _, rows = _q(
                "SELECT ma.nombre Marca, mo.nombre Modelo"
                " FROM MAQUINA m"
                " LEFT JOIN MARCA ma ON ma.clave = m.marca"
                " LEFT JOIN MODELO mo ON mo.codigo = m.modelo"
                " WHERE m.codigo = %s", [codigo_maq]
            )
            if rows and (rows[0]['Marca'] or rows[0]['Modelo']):
                marca = rows[0]['Marca'] or ''
                modelo = rows[0]['Modelo'] or ''
                if es_troubleshooting:
                    query_busqueda = ('%s %s fallas comunes solucion reparacion' % (marca, modelo)).strip()
                else:
                    query_busqueda = ('%s %s especificaciones ficha tecnica' % (marca, modelo)).strip()
                contexto_maquina = (
                    'La maquina %s del sistema es marca "%s", modelo "%s". Usa esto '
                    'como contexto real de lo que se esta buscando.'
                    % (codigo_maq, marca or '(sin marca registrada)', modelo or '(sin modelo registrado)')
                )

    resultados, err = _buscar_web(query_busqueda)
    if err or not resultados:
        return (
            '<p>No pude buscar en internet en este momento'
            + (' (%s).' % _esc(err) if err else ', no encontre resultados relevantes.')
            + ' Puedo seguir ayudandote con lo que ya tenemos registrado en el sistema.</p>'
        )

    fuentes_texto = '\n'.join(
        '%d. %s - %s (%s)' % (i + 1, r['titulo'], r['snippet'], r['url'])
        for i, r in enumerate(resultados)
    )

    system = (
        "Eres Elipse, el asistente de OperaCore. El usuario pidio informacion que "
        "NO esta en la base de datos del sistema, asi que se busco en internet. "
        + (contexto_maquina + ' ' if contexto_maquina else '') +
        "Con base UNICAMENTE en estos resultados de busqueda, responde la pregunta "
        "del usuario en espanol, claro y directo. Resume con tus propias palabras, "
        "no copies texto literal largo. Si los resultados no traen informacion "
        "suficiente, dilo honestamente en vez de inventar datos. No repitas los "
        "links al final, eso ya se muestra aparte."
    )
    user_msg = 'Pregunta: "%s"\n\nResultados de busqueda:\n%s' % (pregunta, fuentes_texto)

    respuesta, err2 = _llamar_groq(system, user_msg, modelo_id, historial=historial,
                                    max_tokens=500, temperature=0.3)
    if err2 and _es_error_conexion(err2):
        return _respuesta_sin_internet(pregunta)

    partes = []
    if respuesta:
        partes.append(_texto_a_html(respuesta))
    fuentes_html = ''.join(
        '<li><a href="%s" target="_blank" rel="noopener">%s</a></li>' % (r['url'], r['titulo'])
        for r in resultados
    )
    partes.append(
        '<p style="margin-top:10px;font-size:12px;color:var(--color-muted,#94a3b8)">'
        '🌐 Fuentes de internet:</p><ul style="font-size:12px">%s</ul>' % fuentes_html
    )
    return ''.join(partes)


# ─────────────────────────────────────────────────────────
# Sugerencia de diagnostico (RF-28 / RNF-Propuesta 1)
# ─────────────────────────────────────────────────────────
# Al capturar un reporte de falla, se consulta el historial de esa MISMA
# maquina (sintomas, causa raiz, severidad, refacciones usadas) y se le pide
# a la IA una causa probable + severidad recomendada. El tecnico SIEMPRE
# puede editar o ignorar la sugerencia -- esto nunca escribe en la BD.
#
# Si no hay conexion/API key, no se cae a un error: se arma una sugerencia
# local con el historial (sin IA, usando similitud de texto) y, si la
# maquina no tiene historial todavia, se cae a un tip pregrabado por
# palabra clave para que la pantalla nunca se vea vacia/rota.

TIPS_PREGRABADOS = [
    # ── Seguridad critica: se revisan PRIMERO, sin importar que mas diga
    # el sintoma. Si el tecnico menciona una explosion o fuego, eso pesa
    # mas que cualquier otra palabra en el texto. ──────────────────────
    {
        'claves': ('explot', 'exploto', 'explosion', 'estallo', 'reven', 'volo en pedazos',
                   'salio disparado', 'salio volando'),
        'severidad': 'CRITI',
        'causa_probable': 'Posible falla catastrofica: ruptura de un componente a presion, '
                           'corto circuito severo o acumulacion de gas/presion. Riesgo de '
                           'seguridad inmediato para el personal.',
        'tip': 'Evacua y acordona el area de inmediato. Corta la alimentacion electrica/'
               'neumatica desde el tablero principal solo si es seguro hacerlo. NO reactives '
               'la maquina ni te acerques hasta que se haga una inspeccion presencial completa.',
    },
    {
        'claves': ('humo', 'humea', 'huele a quemado', 'olor a quemado', 'se incendio',
                   'incendio', 'fuego', 'llamas', 'se prendio en llamas'),
        'severidad': 'CRITI',
        'causa_probable': 'Sobrecalentamiento severo o falla electrica con riesgo real de incendio.',
        'tip': 'Corta la alimentacion de inmediato, aleja al personal y ten a la mano un '
               'extintor para equipo electrico (clase C). No apliques agua sobre el equipo.',
    },
    {
        'claves': ('chispa', 'chisporrote', 'corto circuito', 'se corto', 'olor a quemado electrico'),
        'severidad': 'CRITI',
        'causa_probable': 'Corto circuito o arco electrico en cableado, contactor o tablero.',
        'tip': 'Corta la alimentacion desde el interruptor principal antes de acercarte. No '
               'intervengas el tablero sin bloqueo/etiquetado (LOTO) y equipo de proteccion.',
    },
    # ── Fallas mecanicas / electricas comunes (no urgentes de seguridad) ──
    {
        'claves': ('sobrecalent', 'temperatura', 'calor', 'quemad'),
        'severidad': 'ALTA',
        'causa_probable': 'Posible sobrecalentamiento (ventilacion obstruida, lubricante insuficiente o sobrecarga del motor).',
        'tip': 'Revisa temperatura del motor/servo, estado del lubricante y que las rejillas de ventilacion no esten obstruidas.',
    },
    {
        'claves': ('fuga', 'derrame', 'gotea', 'liquido', 'refrigerante', 'aceite', 'mancha de aceite'),
        'severidad': 'MEDIA',
        'causa_probable': 'Fuga en sellos, empaques o mangueras de la linea de fluido.',
        'tip': 'Ubica el punto exacto de la fuga antes de intervenir; revisa sellos, o-rings y conexiones cercanas.',
    },
    {
        'claves': ('vibra', 'ruido', 'sonido raro', 'sonido extra', 'traba', 'atora', 'rechina',
                   'suena raro', 'hace un ruido'),
        'severidad': 'MEDIA',
        'causa_probable': 'Desalineacion mecanica, rodamiento desgastado o banda floja.',
        'tip': 'Verifica alineacion, tension de bandas y estado de rodamientos/rieles antes de forzar el mecanismo.',
    },
    {
        'claves': ('golpe', 'impacto', 'choco', 'colision', 'se atoro y se rompio'),
        'severidad': 'ALTA',
        'causa_probable': 'Dano mecanico por golpe o colision con otra pieza/equipo.',
        'tip': 'Inspecciona visualmente piezas moviles cercanas al punto de impacto antes de reactivar; busca deformaciones.',
    },
    {
        'claves': ('electric', 'corto', 'no enciende', 'no prende', 'fusible'),
        'severidad': 'CRITI',
        'causa_probable': 'Falla electrica: fusible, contactor o cableado en corto.',
        'tip': 'Corta la alimentacion antes de revisar. Checa fusibles, contactores y continuidad del cableado.',
    },
    {
        'claves': ('congel', 'no responde', 'se traba el software', 'error de software',
                   'pantalla congelada', 'pantalla no responde'),
        'severidad': 'MEDIA',
        'causa_probable': 'Falla de software o del controlador/HMI del equipo.',
        'tip': 'Intenta un reinicio controlado del panel HMI/PLC; si no responde, documenta el mensaje de error visible antes de forzar el apagado.',
    },
    {
        'claves': ('paro total', 'no funciona', 'se detuvo', 'dejo de funcionar', 'apagada'),
        'severidad': 'CRITI',
        'causa_probable': 'Paro total del equipo; requiere diagnostico presencial antes de reanudar produccion.',
        'tip': 'Documenta el estado exacto en que quedo la maquina (pantallas, sonidos, olores) antes de manipularla.',
    },
]
TIP_GENERICO = {
    'severidad': 'MEDIA',
    'causa_probable': 'No hay suficiente informacion para sugerir una causa especifica todavia.',
    'tip': 'Describe el sintoma con mas detalle (que hace/deja de hacer la maquina, desde cuando) para una mejor sugerencia.',
}


def _tip_por_palabra_clave(sintoma):
    s = (sintoma or '').lower()
    for tip in TIPS_PREGRABADOS:
        if any(k in s for k in tip['claves']):
            return tip
    return TIP_GENERICO



def _historial_fallas_maquina(codigo_maquina, limite=8):
    """Ultimos reportes de ESTA maquina, con severidad y refacciones que se
    usaron para resolverlos (via ORDEN_MANTENIMIENTO -> MOVIMIENTO)."""
    cols, rows = _q(
        "SELECT r.numeroRegistro Id, r.asunto Asunto, r.descripcion Descripcion,"
        " r.causaRaiz CausaRaiz, r.fechaCreacion Fecha, r.tiempoParo TiempoParoHrs,"
        " sev.codigo SeveridadCodigo, sev.nombre SeveridadNombre"
        " FROM REPORTE_FALLA r"
        " LEFT JOIN TIPO_SEVERIDAD sev ON sev.codigo = r.tipo_severidad"
        " WHERE r.maquina = %s"
        " ORDER BY r.fechaCreacion DESC LIMIT %s",
        [codigo_maquina, limite]
    )
    if not rows:
        return rows

    ids = [r['Id'] for r in rows]
    placeholders = ','.join(['%s'] * len(ids))
    _, refs = _q(
        "SELECT om.reporte_falla ReporteId,"
        " GROUP_CONCAT(DISTINCT ref.nombre SEPARATOR ', ') Refacciones"
        " FROM ORDEN_MANTENIMIENTO om"
        " JOIN MOVIMIENTO mv ON mv.orden_mantenimiento = om.folio"
        " JOIN REFACCION ref ON ref.numeroRegistro = mv.refaccion"
        " WHERE om.reporte_falla IN (%s)"
        " GROUP BY om.reporte_falla" % placeholders,
        ids
    )
    refs_por_reporte = {r['ReporteId']: r['Refacciones'] for r in refs}
    for r in rows:
        r['Refacciones'] = refs_por_reporte.get(r['Id'], '')
    return rows


def _info_maquina_para_busqueda(codigo_maquina):
    """Nombre/descripcion/marca/modelo/tipo de la maquina, para armar una
    query de internet que si tenga sentido (el codigo interno "MQ003" no
    significa nada para un buscador)."""
    _, rows = _q(
        "SELECT m.nombre Nombre, m.descripcion Descripcion,"
        " ma.nombre Marca, mo.nombre Modelo, tm.nombre Tipo"
        " FROM MAQUINA m"
        " LEFT JOIN MARCA ma ON ma.clave = m.marca"
        " LEFT JOIN MODELO mo ON mo.codigo = m.modelo"
        " LEFT JOIN TIPO_MAQUINA tm ON tm.numeroRegistro = m.tipo_maquina"
        " WHERE m.codigo = %s", [codigo_maquina]
    )
    return rows[0] if rows else {}


SUGERENCIA_WEB_SYSTEM_TPL = """Eres Elipse, asistente tecnico de OperaCore (CMMS de mantenimiento
industrial). Un tecnico esta reportando una falla NUEVA en una maquina que
TODAVIA NO TIENE historial de fallas en el sistema, asi que se busco en
internet informacion general sobre fallas comunes de este tipo de equipo.
Tu trabajo es, con base UNICAMENTE en esos resultados de busqueda y el
sintoma que describe el tecnico, sugerir una causa probable y una severidad.

Responde SOLO con un objeto JSON (nada de texto ni markdown alrededor):
{
  "causa_probable": string, 1-2 oraciones, especifica y tecnica, basada en
    lo que dicen los resultados de busqueda (ej. "Segun fuentes tecnicas,
    un ruido seguido de falla subita en bandas transportadoras suele
    deberse a rotura del rodillo motriz o falla del motorreductor"),
  "severidad": "codigo" (string) EXACTO de la lista de severidades de abajo,
    el que mejor corresponda,
  "justificacion": string breve (1 oracion) de por que esa severidad,
  "confianza": "alta" | "media" | "baja" -- como esto NO es historial real
    de la maquina sino informacion general de internet, normalmente debe
    ser "media" o "baja", nunca "alta"
}

Reglas:
- Usa SOLO codigos de severidad que aparezcan en la lista de abajo.
- No inventes datos que no esten sugeridos por los resultados de busqueda.
- Si los resultados no traen nada util para el sintoma, se honesto y baja la
  confianza a "baja" en vez de inventar una causa.

SEVERIDADES DISPONIBLES (codigo | nombre):
%s

MAQUINA (sin historial en el sistema todavia):
%s

RESULTADOS DE BUSQUEDA:
%s
"""


def _sugerencia_via_web(codigo_maquina, sintoma, severidades, modelo_id):
    """Cuando la maquina no tiene historial local: en vez de saltar directo
    al tip pregrabado por palabra clave, se intenta primero enriquecer la
    sugerencia con una busqueda real en internet (mismo mecanismo que ya usa
    el chat general, _buscar_web) + IA. Regresa un dict listo para la
    Response, o None si la busqueda/IA no dieron nada usable (el caller cae
    entonces al tip pregrabado)."""
    info = _info_maquina_para_busqueda(codigo_maquina)
    nombre = info.get('Nombre') or codigo_maquina
    marca = info.get('Marca') or ''
    modelo = info.get('Modelo') or ''
    tipo = info.get('Tipo') or ''

    descriptor = ' '.join(x for x in (tipo, marca, modelo) if x) or nombre
    query_busqueda = '%s %s causas fallas comunes reparacion' % (descriptor, sintoma[:120])

    resultados, err = _buscar_web(query_busqueda)
    if err or not resultados:
        return None

    fuentes_texto = '\n'.join(
        '%d. %s - %s (%s)' % (i + 1, r['titulo'], r['snippet'], r['url'])
        for i, r in enumerate(resultados)
    )
    info_maquina_texto = 'Nombre: %s | Tipo: %s | Marca: %s | Modelo: %s' % (
        nombre, tipo or '(sin registrar)', marca or '(sin registrar)', modelo or '(sin registrar)'
    )
    system = SUGERENCIA_WEB_SYSTEM_TPL % (
        _catalogo_texto(severidades, ['codigo', 'nombre']),
        info_maquina_texto,
        fuentes_texto,
    )
    crudo, err2 = _llamar_groq(system, sintoma, modelo_id, max_tokens=300, temperature=0.2)
    if err2:
        return None

    campos, _msg = _parsear_json_autofill(
        crudo, claves=('causa_probable', 'severidad', 'justificacion', 'confianza')
    )
    codigos_validos = {s['codigo'] for s in severidades}
    if not campos or not campos.get('causa_probable') or campos.get('severidad') not in codigos_validos:
        return None

    return {
        'fuente': 'web',
        'casos_similares': 0,
        'causa_probable': campos['causa_probable'],
        'severidad': campos['severidad'],
        'justificacion': campos.get('justificacion') or '',
        'confianza': campos.get('confianza') or 'baja',
        'fuentes_web': [{'titulo': r['titulo'], 'url': r['url']} for r in resultados[:3]],
    }


def _severidad_mas_frecuente(historial):
    conteo = {}
    for r in historial:
        c = r.get('SeveridadCodigo')
        if c:
            conteo[c] = conteo.get(c, 0) + 1
    if not conteo:
        return None
    return max(conteo, key=conteo.get)


def _caso_mas_similar(sintoma, historial):
    """Sin IA: compara el sintoma nuevo contra descripcion+causaRaiz de cada
    caso pasado con difflib (ya viene importado arriba) y regresa el mas
    parecido."""
    mejor, mejor_score = None, 0.0
    for r in historial:
        texto = '%s %s' % (r.get('Descripcion') or '', r.get('CausaRaiz') or '')
        score = difflib.SequenceMatcher(None, sintoma.lower(), texto.lower()).ratio()
        if score > mejor_score:
            mejor, mejor_score = r, score
    return mejor


SUGERENCIA_DIAGNOSTICO_SYSTEM_TPL = """Eres Elipse, asistente tecnico de OperaCore (CMMS de mantenimiento
industrial). Un tecnico esta reportando una falla NUEVA en una maquina y te doy
el HISTORIAL REAL de fallas previas de esa MISMA maquina (sintoma, causa raiz,
severidad y refacciones que se usaron para resolverlas). Tu trabajo es sugerir
una causa probable y una severidad para el caso nuevo, basandote en los
patrones del historial.

Responde SOLO con un objeto JSON (nada de texto ni markdown alrededor):
{
  "causa_probable": string, 1-2 oraciones, especifica y tecnica, citando el
    patron del historial en que te basas (ej. "Similar a 3 fallas previas por
    desgaste del rodamiento del eje X"),
  "severidad": "codigo" (string) EXACTO de la lista de severidades de abajo,
    el que mejor corresponda,
  "justificacion": string breve (1 oracion) de por que esa severidad,
  "confianza": "alta" | "media" | "baja" segun que tan parecido es el
    historial al caso nuevo
}

Reglas:
- Usa SOLO codigos de severidad que aparezcan en la lista de abajo.
- Si el historial no se parece al sintoma nuevo, dilo con confianza "baja" en
  vez de inventar una relacion que no existe.
- No prometas nada que no puedas saber por el historial (no diagnostiques
  causas fisicas que no esten sugeridas por los datos).

SEVERIDADES DISPONIBLES (codigo | nombre):
%s

HISTORIAL DE ESTA MAQUINA (mas reciente primero):
%s
"""


def _formatear_historial_para_prompt(historial):
    out = []
    for r in historial:
        out.append(
            '- [%s] %s | causa raiz: %s | severidad: %s | refacciones usadas: %s'
            % (
                r.get('Fecha'), r.get('Descripcion') or r.get('Asunto') or '(sin descripcion)',
                r.get('CausaRaiz') or '(sin registrar)',
                r.get('SeveridadNombre') or '(sin registrar)',
                r.get('Refacciones') or '(ninguna registrada)',
            )
        )
    return '\n'.join(out)


class ElipseSugerenciaDiagnosticoAPIView(APIView):
    """RF-28 + RNF Asistencia Inteligente para Diagnostico de Fallas.

    POST { maquina: "MQ001", sintoma: "la banda se traba y hace ruido...",
           modelo: "groq-llama" (opcional) }

    Responde SIEMPRE 200 con una sugerencia utilizable, nunca un error crudo:
      fuente = "ia"               -> IA con historial real (mejor caso)
      fuente = "historial_local"  -> sin IA (sin internet/API key), pero SI
                                      hay historial: se usa el caso mas
                                      parecido con difflib
      fuente = "web"              -> sin historial de esta maquina, pero se
                                      encontro informacion util buscando en
                                      internet (tipo/marca/modelo + sintoma)
      fuente = "consejo_general"  -> sin historial NI resultados utiles de
                                      internet: tip pregrabado por palabra
                                      clave (nunca deja la pantalla vacia)
    Nunca escribe en la BD; el tecnico decide si usa/edita/ignora.
    """

    def post(self, request):
        codigo_maquina = (request.data.get('maquina') or '').strip()
        sintoma = (request.data.get('sintoma') or '').strip()
        modelo_k = request.data.get('modelo', MODELO_DEFAULT)
        if modelo_k not in MODELOS_IA:
            modelo_k = MODELO_DEFAULT

        if not codigo_maquina or not sintoma:
            return Response({'error': 'Selecciona una maquina y describe el sintoma.'}, status=400)
        sintoma = sintoma[:1000]

        historial = _historial_fallas_maquina(codigo_maquina)
        _, severidades = _q("SELECT codigo, nombre FROM TIPO_SEVERIDAD")

        # Sin historial de esta maquina: en vez de saltar directo al tip
        # pregrabado por palabra clave, primero se intenta enriquecer la
        # sugerencia con una busqueda real en internet (mismo mecanismo que
        # ya usa el chat general) + IA. Si eso no da nada usable (sin
        # internet, sin API key, o la IA no respondio en formato valido),
        # se cae al tip pregrabado -- la pantalla nunca se queda vacia.
        if not historial:
            sugerencia_web = _sugerencia_via_web(codigo_maquina, sintoma, severidades, MODELOS_IA[modelo_k]['id'])
            if sugerencia_web:
                return Response(sugerencia_web)

            tip = _tip_por_palabra_clave(sintoma)
            return Response({
                'fuente': 'consejo_general',
                'casos_similares': 0,
                'causa_probable': tip['causa_probable'],
                'severidad': tip['severidad'],
                'justificacion': 'Esta maquina no tiene fallas registradas todavia; ' + tip['tip'],
            })

        system = SUGERENCIA_DIAGNOSTICO_SYSTEM_TPL % (
            _catalogo_texto(severidades, ['codigo', 'nombre']),
            _formatear_historial_para_prompt(historial),
        )
        modelo_id = MODELOS_IA[modelo_k]['id']
        crudo, err = _llamar_groq(system, sintoma, modelo_id, max_tokens=300, temperature=0.2)

        if not err:
            campos, _msg = _parsear_json_autofill(
                crudo, claves=('causa_probable', 'severidad', 'justificacion', 'confianza')
            )
            codigos_validos = {s['codigo'] for s in severidades}
            if campos and campos.get('causa_probable') and campos.get('severidad') in codigos_validos:
                return Response({
                    'fuente': 'ia',
                    'casos_similares': len(historial),
                    'causa_probable': campos['causa_probable'],
                    'severidad': campos['severidad'],
                    'justificacion': campos.get('justificacion') or '',
                    'confianza': campos.get('confianza') or 'media',
                })
            # la IA respondio pero no en el formato esperado -> cae al modo local

        # Sin internet/API key, o la IA fallo: sugerencia local con el
        # historial real (nunca un error crudo en pantalla).
        caso = _caso_mas_similar(sintoma, historial)
        severidad = (caso or {}).get('SeveridadCodigo') or _severidad_mas_frecuente(historial) or 'MEDIA'
        if caso:
            causa = 'Similar a un caso previo de esta maquina (%s): %s' % (
                caso.get('Fecha'), caso.get('CausaRaiz') or caso.get('Descripcion') or 'sin causa raiz registrada'
            )
        else:
            causa = 'No se pudo comparar automaticamente; revisa el historial de esta maquina abajo.'

        return Response({
            'fuente': 'historial_local',
            'casos_similares': len(historial),
            'causa_probable': causa,
            'severidad': severidad,
            'justificacion': 'Elipse esta sin conexion a la IA ahorita; esto se calculo con el historial local de la maquina.',
        })


# ─────────────────────────────────────────────────────────
# Autocompletado del reporte de falla
# ─────────────────────────────────────────────────────────

AUTOFILL_SYSTEM_TPL = """Eres Elipse, el asistente conversacional de OperaCore (CMMS de
mantenimiento industrial), ayudando a un tecnico a llenar el formulario de
"Reporte de falla" mientras platican. En cada turno debes devolver SOLO un
objeto JSON (nada de texto antes o despues, nada de markdown, nada de
bloques de codigo) con estas claves exactas:

{
  "mensaje": string, tu respuesta conversacional breve (1-2 oraciones, tono
    cercano). Antes de preguntar algo, revisa "CAMPOS YA CONFIRMADOS": jamas
    preguntes de nuevo por algo que ya este ahi. Pregunta SOLO por lo que
    de verdad falte. No repitas literalmente lo que ya dijo el tecnico.
  "asunto": string corto (max 80 caracteres), o null si aun no hay info,
  "descripcion": string tecnica de que sucede (max 500 caracteres), o null,
  "causaRaiz": string, tu mejor hipotesis de causa raiz (max 500
    caracteres), o null,
  "tiempoParo": numero de horas (float, ej 2 o 1.5), o null,
  "fecha": fecha de solucion/atencion en formato YYYY-MM-DD SOLO si el
    tecnico menciono una fecha explicita o relativa ("hoy", "ayer", "el
    lunes"). Si no dijo nada de fechas, regresa null -- el sistema pone la
    fecha de hoy por default, no la inventes tu,
  "maquina": "codigo" (string) de la maquina de la lista de abajo que mejor
    corresponda, o null,
  "tipo_severidad": "codigo" (string) de severidad de la lista de abajo, o
    null,
  "tipo_falla": "numeroRegistro" (numero) del tipo de falla de la lista de
    abajo, o null,
  "estado_reporte": "codigo" (string) del estado del reporte, de la lista
    de abajo. Si el tecnico no dice nada del estado, regresa "ABIER"
    (Abierto) -- es el default logico de un reporte recien levantado, no
    lo dejes null ni lo preguntes salvo que el tecnico mencione otra cosa
    explicitamente (ej. "ya quedo resuelto")
}

CAMPOS YA CONFIRMADOS EN TURNOS ANTERIORES (no vuelvas a preguntar por
estos, solo cambialos si el tecnico los corrige explicitamente ahora):
%s

Reglas estrictas:
- SOLO puedes usar codigos / numeroRegistro que aparezcan tal cual en las
  listas de abajo. Si ninguno encaja, regresa null. NUNCA inventes uno.
- No agregues claves extra ni comentarios. Responde unicamente con el JSON.
- Si un campo ya aparece en CAMPOS YA CONFIRMADOS y el tecnico no lo
  contradice, sigue regresandolo con el mismo valor.
- Nunca inventes datos que el tecnico no haya dado o insinuado.

MAQUINAS DISPONIBLES (codigo | nombre):
%s

SEVERIDADES DISPONIBLES (codigo | nombre):
%s

TIPOS DE FALLA DISPONIBLES (numeroRegistro | nombre):
%s

ESTADOS DE REPORTE DISPONIBLES (codigo | nombre):
%s
"""


def _resolver_crear_reporte_falla(pregunta, modelo_key, historial=None):
    """Levanta un reporte de falla guiado desde el chat general: entiende la
    descripcion, propone los campos y devuelve un boton que lleva al modulo
    de fallas con el formulario ya lleno. NUNCA escribe en la BD."""
    modelo_id = MODELOS_IA.get(modelo_key, MODELOS_IA[MODELO_DEFAULT])['id']

    _, maquinas = _q("SELECT codigo, nombre FROM MAQUINA")
    _, severidades = _q("SELECT codigo, nombre FROM TIPO_SEVERIDAD")
    _, tipos_falla = _q("SELECT numeroRegistro, nombre FROM TIPO_FALLA")
    _, estados = _q("SELECT codigo, nombre FROM EDO_REPORTE")

    system = AUTOFILL_SYSTEM_TPL % (
        _texto_campos_confirmados(None),
        _catalogo_texto(maquinas, ['codigo', 'nombre']),
        _catalogo_texto(severidades, ['codigo', 'nombre']),
        _catalogo_texto(tipos_falla, ['numeroRegistro', 'nombre']),
        _catalogo_texto(estados, ['codigo', 'nombre']),
    )
    crudo, err = _llamar_groq(system, pregunta, modelo_id, historial=historial, max_tokens=500, temperature=0.3)
    if err:
        if _es_error_conexion(err):
            # Sin internet/API key: en vez de dejar el formulario vacio,
            # se intenta una extraccion local (sin IA, menos precisa).
            campos, mensaje = _autofill_local(pregunta, maquinas, severidades, tipos_falla, estados)
            for k, v in (campos_previos or {}).items():
                if campos.get(k) in (None, '') and v not in (None, ''):
                    campos[k] = v
            if not campos.get('fecha'):
                campos['fecha'] = date.today().isoformat()
            return Response({'campos': campos, 'mensaje': mensaje, 'fuente': 'local'})
        return Response({'error': err}, status=502)

    campos, mensaje = _parsear_json_autofill(crudo)
    if campos is None:
        return '<p>No logre entender bien la falla, me das un poco mas de detalle?</p>'
    if not campos.get('fecha'):
        campos['fecha'] = date.today().isoformat()

    campos_b64 = base64.urlsafe_b64encode(
        json.dumps(campos, ensure_ascii=False).encode('utf-8')
    ).decode('ascii')

    resumen = ''.join(
        '<li><strong>%s:</strong> %s</li>' % (_esc(k), _esc(v))
        for k, v in campos.items() if v not in (None, '')
    )
    return (
        '<p>%s</p>'
        '<ul style="font-size:12px;color:var(--color-muted,#94a3b8);margin:6px 0 10px">%s</ul>'
        '<button type="button" class="elipse-chip" '
        "onclick=\"window.elipseIrAModulo('/fallas/reporte/', '%s')\">"
        '📄 Abrir formulario ya llenado</button>'
        % (_esc(mensaje) if mensaje else 'Esto entendi, revisalo en el formulario:', resumen, campos_b64)
    )


class ElipseAutocompletarFallaAPIView(APIView):
    """Toma una descripcion libre de una falla ('la banda del pick and place
    se traba, lleva 2 horas parada...') y regresa un JSON con los campos
    sugeridos para el formulario de 'Reporte de falla'.

    Esto NUNCA escribe en la base de datos: solo propone texto para que el
    tecnico lo revise, ajuste y mande el mismo desde el formulario normal."""

    def post(self, request):
        texto = (request.data.get('texto') or '').strip()
        if not texto:
            return Response({'error': 'Describe la falla primero.'}, status=400)
        texto = texto[:2000]

        modelo_k = request.data.get('modelo', MODELO_DEFAULT)
        if modelo_k not in MODELOS_IA:
            modelo_k = MODELO_DEFAULT

        historial = request.data.get('historial') or []
        campos_previos = request.data.get('campos_previos') or {}
        maquinas = request.data.get('maquinas')
        severidades = request.data.get('severidades')
        tipos_falla = request.data.get('tipos_falla')
        estados = request.data.get('estados')

        system = AUTOFILL_SYSTEM_TPL % (
            _texto_campos_confirmados(campos_previos, maquinas, severidades, tipos_falla, estados),
            _catalogo_texto(maquinas, ['codigo', 'nombre']),
            _catalogo_texto(severidades, ['codigo', 'nombre']),
            _catalogo_texto(tipos_falla, ['numeroRegistro', 'nombre']),
            _catalogo_texto(estados, ['codigo', 'nombre']),
        )

        modelo_id = MODELOS_IA[modelo_k]['id']
        crudo, err = _llamar_groq(system, texto, modelo_id, historial=historial, max_tokens=500, temperature=0.3)
        if err:
            if _es_error_conexion(err):
                # Sin internet/API key: en vez de dejar el formulario vacio,
                # se intenta una extraccion local (sin IA, menos precisa).
                campos, mensaje = _autofill_local(texto, maquinas, severidades, tipos_falla, estados)
                for k, v in campos_previos.items():
                    if campos.get(k) in (None, '') and v not in (None, ''):
                        campos[k] = v
                if not campos.get('fecha'):
                    campos['fecha'] = date.today().isoformat()
                return Response({'campos': campos, 'mensaje': mensaje, 'fuente': 'local'})
            return Response({'error': err}, status=502)

        campos, mensaje = _parsear_json_autofill(crudo)
        if campos is None:
            return Response(
                {'error': 'No pude interpretar bien esa descripcion, intenta darle un poco mas de detalle.'},
                status=502,
            )

        # Red de seguridad: si el modelo "olvido" devolver algo que ya
        # estaba confirmado en un turno anterior, lo rellenamos aqui para
        # que el campo nunca desaparezca ni se vuelva a preguntar.
        for k, v in campos_previos.items():
            if campos.get(k) in (None, '') and v not in (None, ''):
                campos[k] = v

        if not campos.get('fecha'):
            campos['fecha'] = date.today().isoformat()
        if not campos.get('estado_reporte'):
            estados_validos = {e.get('codigo') for e in (estados or []) if isinstance(e, dict)}
            if 'ABIER' in estados_validos:
                campos['estado_reporte'] = 'ABIER'

        return Response({'campos': campos, 'mensaje': mensaje or ''})


# ─────────────────────────────────────────────────────────
# Autocompletado de la orden de mantenimiento
# ─────────────────────────────────────────────────────────

AUTOFILL_ORDEN_SYSTEM_TPL = """Eres Elipse, el asistente conversacional de OperaCore (CMMS de
mantenimiento industrial), ayudando a un tecnico/administrador a llenar el
formulario de "Nueva orden de mantenimiento" mientras platican. En cada
turno debes devolver SOLO un objeto JSON (nada de texto antes o despues,
nada de markdown, nada de bloques de codigo) con estas claves exactas:

{
  "mensaje": string, tu respuesta conversacional breve (1-2 oraciones, tono
    cercano). Si ya tienes lo esencial (maquina, descripcion) confirma y
    pregunta por lo que falte, ej. "es preventivo o correctivo? y para
    cuando la programamos?". No repitas literalmente lo que ya dijo el
    usuario.
  "descripcion": string de que se necesita hacer en la maquina (max 500
    caracteres), o null si aun no hay info,
  "maquina": "codigo" (string) de la maquina de la lista de abajo que mejor
    corresponda, o null,
  "tipo_mantenimiento": "codigo" (string) del tipo de mantenimiento de la
    lista de abajo que mejor corresponda (ej. si el usuario dice "se
    descompuso"/"fallo" es CORRE=Correctivo; si dice "programada"/"rutina"
    es PREVE=Preventivo), o null,
  "fechaprogramada": fecha en formato YYYY-MM-DD SOLO si el usuario
    menciono una fecha explicita o relativa ("manana", "el lunes", "en dos
    semanas"). Si no dijo nada de fechas, regresa null -- el formulario se
    deja sin fecha programada por default, no la inventes tu
}

Reglas estrictas:
- SOLO puedes usar codigos que aparezcan tal cual en las listas de abajo.
  Si ninguno encaja, regresa null. NUNCA inventes uno.
- No agregues claves extra ni comentarios. Responde unicamente con el JSON.
- Si un campo ya se lleno en un turno anterior (viene en el historial) y el
  usuario no lo contradice, sigue regresandolo con el mismo valor.
- Nunca inventes datos que el usuario no haya dado o insinuado.
- Esto NUNCA crea la orden en la base de datos, solo propone texto para el
  formulario -- el usuario sigue siendo quien da "Crear".
- IMPORTANTE: si el texto menciona una maquina o tipo de mantenimiento que
  NO aparece en las listas de abajo, dejalo en null como indica la regla de
  arriba, PERO avisa brevemente en "mensaje" cual dato no se pudo
  relacionar para que el usuario lo seleccione manualmente.

MAQUINAS DISPONIBLES (codigo | nombre):
%s

TIPOS DE MANTENIMIENTO DISPONIBLES (codigo | nombre):
%s
"""


def _resolver_crear_orden_mantenimiento(pregunta, modelo_key, historial=None):
    """Levanta una orden de mantenimiento guiada desde el chat general:
    entiende que se necesita, propone los campos y devuelve un boton que
    lleva al modulo de mantenimiento con el formulario "Nueva orden" ya
    lleno. NUNCA escribe en la BD."""
    modelo_id = MODELOS_IA.get(modelo_key, MODELOS_IA[MODELO_DEFAULT])['id']

    _, maquinas = _q("SELECT codigo, nombre FROM MAQUINA")
    _, tipos_mantenimiento = _q("SELECT codigo, nombre FROM TIPO_MANTENIMIENTO")

    system = AUTOFILL_ORDEN_SYSTEM_TPL % (
        _catalogo_texto(maquinas, ['codigo', 'nombre']),
        _catalogo_texto(tipos_mantenimiento, ['codigo', 'nombre']),
    )
    crudo, err = _llamar_groq(system, pregunta, modelo_id, historial=historial, max_tokens=400, temperature=0.3)
    if err:
        if _es_error_conexion(err):
            return _respuesta_sin_internet(pregunta)
        return '<p class="msg-error">%s</p>' % _esc(err)

    campos, mensaje = _parsear_json_autofill(
        crudo, claves=('descripcion', 'maquina', 'tipo_mantenimiento', 'fechaprogramada')
    )
    if campos is None:
        return '<p>No logre entender bien que orden necesitas, me das un poco mas de detalle?</p>'

    campos_b64 = base64.urlsafe_b64encode(
        json.dumps(campos, ensure_ascii=False).encode('utf-8')
    ).decode('ascii')

    resumen = ''.join(
        '<li><strong>%s:</strong> %s</li>' % (_esc(k), _esc(v))
        for k, v in campos.items() if v not in (None, '')
    )
    return (
        '<p>%s</p>'
        '<ul style="font-size:12px;color:var(--color-muted,#94a3b8);margin:6px 0 10px">%s</ul>'
        '<button type="button" class="elipse-chip" '
        "onclick=\"window.elipseIrAModulo('/mantenimiento/', '%s')\">"
        '🛠️ Abrir formulario ya llenado</button>'
        % (_esc(mensaje) if mensaje else 'Esto entendi, revisalo en el formulario:', resumen, campos_b64)
    )


class ElipseAutocompletarOrdenAPIView(APIView):
    """Toma una descripcion libre de lo que necesita una orden de
    mantenimiento ('hay que revisar la banda de MAQ003, esta rechinando')
    y regresa un JSON con los campos sugeridos para el formulario "Nueva
    orden". Mismo patron que ElipseAutocompletarFallaAPIView: esto NUNCA
    escribe en la base de datos, solo propone texto para que el usuario lo
    revise, ajuste y mande el mismo desde el formulario normal."""

    def post(self, request):
        texto = (request.data.get('texto') or '').strip()
        if not texto:
            return Response({'error': 'Describe la orden primero.'}, status=400)
        texto = texto[:2000]

        modelo_k = request.data.get('modelo', MODELO_DEFAULT)
        if modelo_k not in MODELOS_IA:
            modelo_k = MODELO_DEFAULT

        historial = request.data.get('historial') or []

        system = AUTOFILL_ORDEN_SYSTEM_TPL % (
            _catalogo_texto(request.data.get('maquinas'), ['codigo', 'nombre']),
            _catalogo_texto(request.data.get('tipos_mantenimiento'), ['codigo', 'nombre']),
        )

        modelo_id = MODELOS_IA[modelo_k]['id']
        crudo, err = _llamar_groq(system, texto, modelo_id, historial=historial, max_tokens=400, temperature=0.3)
        if err:
            if _es_error_conexion(err):
                return Response(
                    {'error': 'Elipse no tiene conexion ahorita. Puedes llenar el formulario a mano mientras tanto.'},
                    status=503,
                )
            return Response({'error': err}, status=502)

        campos, mensaje = _parsear_json_autofill(
            crudo, claves=('descripcion', 'maquina', 'tipo_mantenimiento', 'fechaprogramada')
        )
        if campos is None:
            return Response(
                {'error': 'No pude interpretar bien esa descripcion, intenta darle un poco mas de detalle.'},
                status=502,
            )

        return Response({'campos': campos, 'mensaje': mensaje or ''})


# ─────────────────────────────────────────────────────────
# Vista principal
# ─────────────────────────────────────────────────────────

class ElipseEstadoAPIView(APIView):
    """Chequeo rapido y barato de si Groq (la IA) esta disponible: valida
    que haya API key y hace un GET a /models (NO genera texto, no gasta
    tokens de completion como el chat) con timeout corto."""

    def get(self, request):
        api_key = settings.GROQ_API_KEY
        if not api_key:
            return Response({'ok': False, 'motivo': 'sin_api_key'})

        req = urllib.request.Request(
            'https://api.groq.com/openai/v1/models',
            headers={
                'Authorization': 'Bearer ' + api_key,
                # Mismo User-Agent que _llamar_groq: sin este header,
                # urllib manda "Python-urllib/x.y" por default y Groq
                # (detras de Cloudflare) lo bloquea como bot con 403,
                # aunque la API si este disponible (falso "no disponible").
                'User-Agent': 'Mozilla/5.0 (compatible; OperaCore-Elipse/2.0)',
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=8) as res:
                ok = res.status == 200
        except Exception:
            ok = False

        return Response({'ok': ok})

class ElipseSugerenciasAPIView(APIView):
    """Devuelve PREGUNTAS_RAPIDAS para que el client arme los chips."""

    def get(self, request):
        return Response({'sugerencias': PREGUNTAS_RAPIDAS})


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
        if intent == 'buscar_web':
            html = _resolver_busqueda_web(pregunta, modelo_k, historial=historial)
        elif intent == 'crear_reporte_falla':
            html = _resolver_crear_reporte_falla(pregunta, modelo_k, historial=historial)
        elif intent == 'crear_orden_mantenimiento':
            html = _resolver_crear_orden_mantenimiento(pregunta, modelo_k, historial=historial)
        else:
            try:
                html = _resolve(intent, pregunta)
            except Exception as e:
                html = '<p class="msg-error">Error consultando la base de datos: %s</p>' % _esc(e)

            if html is None:
                html = _ai_con_sql(pregunta, modelo_k, historial=historial)

        return Response({'html': html, 'intent': intent, 'modelo': MODELOS_IA[modelo_k]['label']})