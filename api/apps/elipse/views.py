"""
elipse_views (api) - Asistente Elipse para OperaCore CMMS.
Version 1: charla + consultas basicas sobre TRABAJADOR (lo unico que ya
tiene modelos reales). Conforme agregues maquinaria/fallas/mantenimiento,
solo hay que sumar bloques nuevos en SCHEMA y en _resolve().
"""
import json
import re
import urllib.request
import urllib.error

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.usuarios.models import Trabajador, Rol, Especialidad

# ── Modelos de IA disponibles (Groq) ──────────────────────
MODELOS_IA = {
    'groq-llama':   {'id': 'llama-3.3-70b-versatile', 'label': 'Llama 3.3 70B', 'desc': 'Potente y rapido'},
    'groq-llama-8': {'id': 'llama-3.1-8b-instant',    'label': 'Llama 3.1 8B',  'desc': 'Ultra rapido'},
}
MODELO_DEFAULT = 'groq-llama'

INFO_OPERACORE = """
<p><strong>⚙️ OperaCore CMMS</strong></p>
<p>Sistema de gestión de mantenimiento (CMMS) todavía en desarrollo. Por ahora tiene
funcional el módulo de <strong>usuarios/trabajadores</strong>; los módulos de
maquinaria, mantenimiento, fallas, inventario e indicadores se están construyendo.</p>
<p><strong>Elipse</strong> es el asistente de IA interno de OperaCore. Hoy puede
responder sobre trabajadores registrados; pronto podrá responder sobre máquinas,
órdenes de mantenimiento, fallas e inventario.</p>
"""

CAPACIDADES = """
<p><strong>🤖 ¿Qué puedo hacer yo, Elipse?</strong></p>
<p>Todavía estoy en preparación junto con el sistema. Por ahora puedo:</p>
<ul>
  <li>👤 <em>"Lista de trabajadores"</em> / <em>"trabajadores activos"</em></li>
  <li>🔎 <em>"Busca al trabajador Juan Pérez"</em></li>
  <li>🏷️ <em>"Cuántos trabajadores hay por rol"</em></li>
  <li>💬 Conversación libre sobre el sistema</li>
</ul>
<p style="color:var(--color-muted, #94a3b8);font-size:12px;">
  ⚠️ Solo puedo <strong>consultar</strong> datos, nunca modificar ni borrar nada.
</p>
"""

SYSTEM_PROMPT = (
    "Eres Elipse, el asistente de inteligencia artificial de OperaCore, un sistema "
    "de gestion de mantenimiento (CMMS) que todavia esta en desarrollo. "
    "Por ahora solo el modulo de trabajadores/usuarios tiene datos reales; los "
    "modulos de maquinaria, mantenimiento, fallas, inventario e indicadores estan "
    "en construccion y debes decirlo claramente si preguntan por ellos. "
    "Responde en espanol, claro y conciso, en tono profesional pero cercano."
)


# ── Utilidades ─────────────────────────────────────────────

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
            'User-Agent': 'Mozilla/5.0 (compatible; OperaCore-Elipse/1.0)',
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


def _texto_a_html(text):
    if not text:
        return ''
    parts = []
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
        parts.append('<p>%s</p>' % line)
    return ''.join(parts)


def _tabla_trabajadores(qs):
    if not qs:
        return '<em>No se encontraron trabajadores.</em>'
    filas = ''.join(
        '<tr><td>%s</td><td>%s %s</td><td>%s</td><td>%s</td></tr>' % (
            t.numeroNomina, t.nombre, t.apellidoPat,
            t.rol.nombre if t.rol else '-',
            'Activo' if t.actividad else 'Inactivo',
        )
        for t in qs
    )
    return (
        '<table><thead><tr><th>Nómina</th><th>Nombre</th><th>Rol</th><th>Estado</th></tr></thead>'
        '<tbody>%s</tbody></table>' % filas
    )


# ── Intents (consultas ya resueltas sin gastar IA) ─────────
# A medida que agregues maquinaria/mantenimiento/fallas/inventario, ve
# sumando bloques "if has(...)" aqui, tal como se hizo en RBE.

def _intent(q_orig):
    q = q_orig.lower()
    tr = str.maketrans('áéíóúñ', 'aeioun')
    q = q.translate(tr)

    def has(*ws):
        return any(w in q for w in ws)

    if has('que puedes hacer', 'que sabes hacer', 'capacidades', 'ayuda'):
        return 'capacidades'
    if has('que es operacore', 'sobre operacore', 'info de operacore', 'quien eres'):
        return 'info_sistema'
    if has('lista de trabajadores', 'trabajadores activos', 'listar trabajadores',
           'todos los trabajadores'):
        return 'trabajadores_lista'
    if has('cuantos trabajadores', 'trabajadores por rol'):
        return 'trabajadores_por_rol'
    if has('busca', 'buscar') and has('trabajador'):
        return 'trabajador_buscar'
    return 'ai'


def _resolve(intent, pregunta):
    if intent == 'capacidades':
        return CAPACIDADES
    if intent == 'info_sistema':
        return INFO_OPERACORE
    if intent == 'trabajadores_lista':
        qs = Trabajador.objects.filter(actividad=True).select_related('rol')[:50]
        return '<p><strong>Trabajadores activos:</strong></p>%s' % _tabla_trabajadores(qs)
    if intent == 'trabajadores_por_rol':
        from django.db.models import Count
        datos = (Trabajador.objects.values('rol__nombre')
                 .annotate(total=Count('numeroNomina')).order_by('-total'))
        if not datos:
            return '<em>No hay trabajadores registrados todavía.</em>'
        filas = ''.join(
            '<tr><td>%s</td><td>%s</td></tr>' % (d['rol__nombre'] or 'Sin rol', d['total'])
            for d in datos
        )
        return ('<p><strong>Trabajadores por rol:</strong></p>'
                '<table><thead><tr><th>Rol</th><th>Total</th></tr></thead>'
                '<tbody>%s</tbody></table>' % filas)
    if intent == 'trabajador_buscar':
        m = re.search(r'trabajador(?:a)?\s+([a-záéíóúñ ]{3,})', pregunta.lower())
        nombre = m.group(1).strip() if m else None
        if not nombre:
            return '<p>Dime el nombre, ej: <em>"busca al trabajador Juan Pérez"</em></p>'
        qs = Trabajador.objects.filter(nombre__icontains=nombre.split()[0])[:20]
        return '<p><strong>Resultados para "%s":</strong></p>%s' % (nombre, _tabla_trabajadores(qs))
    return None  # → cae a la IA conversacional


# ── Vista principal ─────────────────────────────────────────

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
        html = _resolve(intent, pregunta)

        if html is None:
            respuesta, err = _llamar_groq(
                SYSTEM_PROMPT, pregunta, MODELOS_IA[modelo_k]['id'], historial=historial
            )
            if err:
                return Response({'error': err}, status=500)
            html = _texto_a_html(respuesta)

        return Response({'html': html, 'intent': intent, 'modelo': MODELOS_IA[modelo_k]['label']})
