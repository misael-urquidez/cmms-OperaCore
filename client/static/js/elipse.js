/* ==========================================================================
   Elipse — logica del chat.

   Tres responsabilidades:
   1. Enviar preguntas al client (que las reenvia al api/) y pintar la respuesta.
   2. Animar esa respuesta: el texto se escribe, las tablas entran en cascada.
   3. Memoria en localStorage: historial de la conversacion + datos que el
      usuario pidio recordar explicitamente ("recuerda que...").

   Nada de esto toca la base de datos. Si el usuario limpia el navegador,
   Elipse simplemente vuelve a empezar en blanco.
   ========================================================================== */

/* Navega a un modulo con los campos que Elipse propuso, codificados en la
   URL. La invoca el boton "Abrir formulario ya llenado" que llega dentro del
   HTML de la respuesta, asi que tiene que vivir en el scope global (fuera
   del IIFE de abajo). No guarda nada: el formulario destino solo se
   prellena, el usuario sigue siendo quien envia. */
window.elipseIrAModulo = function (url, camposB64) {
    var sep = url.indexOf('?') === -1 ? '?' : '&';
    window.location.href = url + sep + 'elipse=' + encodeURIComponent(camposB64);
};

(function () {
    'use strict';

    // ── Config ───────────────────────────────────────────────
    const LS_HISTORIAL = 'elipse_historial_v1';
    const LS_MEMORIA   = 'elipse_memoria_v1';
    const MAX_HISTORIAL = 40;   // mensajes guardados (20 intercambios)
    const MAX_MEMORIA   = 20;   // datos recordados
    const MAX_MEM_CHARS = 200;  // por dato, para no inflar el prompt
    const MS_POR_CHAR   = 18;   // velocidad del efecto de escritura
    const MAX_MS_BLOQUE = 1800; // tope: un parrafo largo no tarda eternamente

    const cfg = window.ELIPSE_CONFIG || {};
    const sinMovimiento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // ── Estado ───────────────────────────────────────────────
    let ocupado = false;
    let historial = [];   // {role, content, html}
    let memoria = [];     // {id, texto, ts}
    let saltarAnim = null; // fn para terminar la animacion en curso de golpe

    // ── Elementos ────────────────────────────────────────────
    const $ = (id) => document.getElementById(id);
    const elMensajes = $('elipseMessages');
    const elInput    = $('elipseInput');
    const elSend     = $('elipseSend');
    const elJump     = $('elipseJump');
    const elMemPanel = $('elipseMemPanel');
    const elMemList  = $('elipseMemList');
    const elMemCount = $('elipseMemCount');
    const elAdjuntarBtn = $("elipseAdjuntarBtn");
    const elAdjuntarInput = $("elipseAdjuntarInput");

    // ─────────────────────────────────────────────────────────
    // Utilidades
    // ─────────────────────────────────────────────────────────

    function esc(s) {
        return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    /* localStorage puede fallar (modo privado, cupo lleno). Nunca queremos
       que eso tumbe el chat, asi que todo acceso va envuelto. */
    function leerLS(clave, porDefecto) {
        try {
            const raw = localStorage.getItem(clave);
            return raw ? JSON.parse(raw) : porDefecto;
        } catch (e) {
            return porDefecto;
        }
    }

    function guardarLS(clave, valor) {
        try {
            localStorage.setItem(clave, JSON.stringify(valor));
        } catch (e) {
            /* Sin espacio o sin permiso: seguimos en memoria volatil. */
        }
    }

    function toast(texto) {
        const t = document.createElement('div');
        t.className = 'elipse-toast';
        t.textContent = texto;
        document.body.appendChild(t);
        setTimeout(() => t.remove(), 2600);
    }

    // ─────────────────────────────────────────────────────────
    // Scroll
    // ─────────────────────────────────────────────────────────

    /* Solo auto-scrolleamos si el usuario ya estaba hasta abajo. Si subio a
       leer algo, respetamos su posicion y le ofrecemos el boton de bajar. */
    function estaAbajo() {
        return elMensajes.scrollHeight - elMensajes.scrollTop - elMensajes.clientHeight < 80;
    }

    function bajar(forzar) {
        if (forzar || estaAbajo()) {
            elMensajes.scrollTop = elMensajes.scrollHeight;
            elJump.classList.remove('is-visible');
        } else {
            elJump.classList.add('is-visible');
        }
    }

    elMensajes.addEventListener('scroll', () => {
        if (estaAbajo()) elJump.classList.remove('is-visible');
    });

    elJump.addEventListener('click', () => bajar(true));

    // ─────────────────────────────────────────────────────────
    // Render de mensajes
    // ─────────────────────────────────────────────────────────

    function quitarBienvenida() {
        const w = $('elipseWelcome');
        if (w) w.remove();
    }

    /* Crea la burbuja vacia y devuelve el nodo donde va el contenido.
       Separar la creacion del llenado es lo que permite animar despues. */
    function crearBurbuja(rol, restaurado) {
        quitarBienvenida();
        const d = document.createElement('div');
        d.className = 'elipse-msg elipse-msg--' + rol + (restaurado ? ' elipse-msg--restored' : '');
        const nombre = rol === 'user' ? (cfg.nombreUsuario || 'Tú') : 'Elipse';
        d.innerHTML = '<div class="elipse-msg__name"></div><div class="elipse-msg__bubble"></div>';
        d.querySelector('.elipse-msg__name').textContent = nombre;
        elMensajes.appendChild(d);
        return d.querySelector('.elipse-msg__bubble');
    }

    function addMsg(rol, html, restaurado) {
        const b = crearBurbuja(rol, restaurado);
        b.innerHTML = html;
        prepararAnimacionesInternas(b, !restaurado);
        bajar();
        return b;
    }

    /* Numera filas de tabla, stat-cards y chips con --i para que el CSS las
       escalone. Si no queremos animar (historial restaurado), las marca como
       ya visibles quitandoles la animacion. */
    function prepararAnimacionesInternas(root, animar) {
        const grupos = [
            root.querySelectorAll('tbody tr'),
            root.querySelectorAll('.stat-card'),
            root.querySelectorAll('.elipse-chip'),
        ];
        grupos.forEach((lista) => {
            lista.forEach((el, i) => {
                if (animar && !sinMovimiento) {
                    el.style.setProperty('--i', i);
                } else {
                    el.style.animation = 'none';
                }
            });
        });
    }

    // ─────────────────────────────────────────────────────────
    // Efecto de escritura
    // ─────────────────────────────────────────────────────────

    /* El backend manda HTML ya armado (tablas, cards, badges), asi que no se
       puede hacer un typewriter ingenuo sobre el string: partiria las
       etiquetas a media palabra.

       En vez de eso parseamos el HTML y recorremos los hijos de primer nivel:
       - <p>, <li>, <h*> y texto suelto  -> se escriben caracter por caracter
       - <table>, .stat-cards, <details> -> aparecen de golpe con su animacion

       Devuelve una promesa que resuelve al terminar (o al saltar). */
    function escribirHTML(burbuja, html) {
        return new Promise((resolve) => {
            const plantilla = document.createElement('template');
            plantilla.innerHTML = html;
            const bloques = Array.from(plantilla.content.childNodes);

            if (sinMovimiento) {
                burbuja.innerHTML = html;
                prepararAnimacionesInternas(burbuja, false);
                bajar();
                resolve();
                return;
            }

            let cancelado = false;

            // Salta al resultado final: pinta todo y corta la animacion.
            function saltar() {
                if (cancelado) return;
                cancelado = true;
                saltarAnim = null;
                burbuja.innerHTML = html;
                prepararAnimacionesInternas(burbuja, false);
                bajar();
                resolve();
            }
            saltarAnim = saltar;

            let idx = 0;

            function siguienteBloque() {
                if (cancelado) return;
                if (idx >= bloques.length) {
                    saltarAnim = null;
                    bajar();
                    resolve();
                    return;
                }
                const nodo = bloques[idx++];

                // Nodos de texto vacios entre etiquetas: se ignoran.
                if (nodo.nodeType === Node.TEXT_NODE && !nodo.textContent.trim()) {
                    siguienteBloque();
                    return;
                }

                const clon = nodo.cloneNode(true);
                const esTexto = nodo.nodeType === Node.TEXT_NODE ||
                    /^(P|LI|H1|H2|H3|H4|EM|STRONG|SPAN)$/.test(nodo.nodeName);

                if (!esTexto) {
                    // Estructura: entra completa con su animacion CSS.
                    burbuja.appendChild(clon);
                    if (clon.nodeType === Node.ELEMENT_NODE) {
                        prepararAnimacionesInternas(clon, true);
                        // El propio contenedor tambien entra suave.
                        clon.style.animation = 'elipse-row-in 0.3s ease both';
                    }
                    bajar();
                    setTimeout(siguienteBloque, 120);
                    return;
                }

                // Texto: lo escribimos progresivamente.
                escribirNodo(burbuja, clon, siguienteBloque, () => cancelado);
            }

            siguienteBloque();
        });
    }

    /* Escribe un nodo de texto (o un elemento con texto dentro) caracter por
       caracter, conservando su HTML interno: primero lo insertamos vacio y
       luego revelamos su textContent progresivamente sobre una copia. */
    function escribirNodo(burbuja, nodo, alTerminar, estaCancelado) {
        const esElemento = nodo.nodeType === Node.ELEMENT_NODE;
        const htmlFinal = esElemento ? nodo.innerHTML : null;
        const texto = nodo.textContent || '';

        // Contenedor real donde se va escribiendo.
        let destino;
        if (esElemento) {
            destino = nodo;
            destino.textContent = '';
            destino.style.animation = 'elipse-row-in 0.24s ease both';
        } else {
            destino = document.createElement('span');
        }
        burbuja.appendChild(destino);

        const caret = document.createElement('span');
        caret.className = 'elipse-caret';
        destino.appendChild(caret);

        // Si el bloque es muy largo aceleramos para no pasar del tope.
        const paso = Math.max(1, Math.ceil(texto.length * MS_POR_CHAR / MAX_MS_BLOQUE));
        let i = 0;
        let ultimo = 0;

        function frame(ts) {
            if (estaCancelado()) return;
            if (!ultimo) ultimo = ts;

            if (ts - ultimo >= MS_POR_CHAR) {
                ultimo = ts;
                i = Math.min(texto.length, i + paso);
                caret.remove();
                destino.textContent = texto.slice(0, i);
                if (i < texto.length) destino.appendChild(caret);
                bajar();
            }

            if (i < texto.length) {
                requestAnimationFrame(frame);
            } else {
                // Restauramos el HTML real (negritas, <em>, <code>...).
                if (esElemento && htmlFinal !== null) destino.innerHTML = htmlFinal;
                alTerminar();
            }
        }
        requestAnimationFrame(frame);
    }

    // Click en el chat o Esc: salta la animacion en curso.
    elMensajes.addEventListener('click', (e) => {
        // No robamos el click de chips ni de enlaces.
        if (e.target.closest('button, a, summary')) return;
        if (saltarAnim) saltarAnim();
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && saltarAnim) saltarAnim();
    });

    // ─────────────────────────────────────────────────────────
    // Indicador de "pensando"
    // ─────────────────────────────────────────────────────────

    /* Muestra los 3 puntos y va cambiando el texto para que se note que sigue
       trabajando. El API responde de una sola vez, asi que las fases son
       estimadas por tiempo, no reportadas por el servidor. */
    function mostrarPensando() {
        const b = crearBurbuja('ai', false);
        b.innerHTML =
            '<span class="elipse-typing">' +
            '<span class="elipse-typing__dots"><i></i><i></i><i></i></span>' +
            '<span class="elipse-typing__texto">pensando…</span>' +
            '</span>';
        bajar(true);

        const txt = b.querySelector('.elipse-typing__texto');
        const t1 = setTimeout(() => { txt.textContent = 'consultando la base de datos…'; }, 900);
        const t2 = setTimeout(() => { txt.textContent = 'esto está tardando un poco…'; }, 2500);

        return {
            burbuja: b,
            limpiar() {
                clearTimeout(t1);
                clearTimeout(t2);
                b.innerHTML = '';
            },
            quitar() {
                clearTimeout(t1);
                clearTimeout(t2);
                b.closest('.elipse-msg').remove();
            },
        };
    }

    // ─────────────────────────────────────────────────────────
    // Memoria: datos que el usuario pidio recordar
    // ─────────────────────────────────────────────────────────

    /* Solo memoria explicita. Dejar que la IA decida sola que guardar es
       impredecible y dificil de depurar, asi que se queda fuera a proposito. */
    const RE_RECUERDA = /^\s*(?:recuerda|recuérdate|recuerdate|acuérdate|acuerdate|apunta|anota)\s+(?:que\s+|de\s+que\s+)?(.{3,})$/i;

    function detectarRecuerda(texto) {
        const m = texto.match(RE_RECUERDA);
        return m ? m[1].trim().replace(/[.\s]+$/, '') : null;
    }

    function agregarMemoria(texto) {
        const limpio = texto.slice(0, MAX_MEM_CHARS);
        // Evitamos duplicados exactos.
        if (memoria.some((m) => m.texto.toLowerCase() === limpio.toLowerCase())) return false;
        memoria.push({ id: 'm' + memoria.length + '_' + elMensajes.childElementCount, texto: limpio });
        if (memoria.length > MAX_MEMORIA) memoria = memoria.slice(-MAX_MEMORIA);
        guardarLS(LS_MEMORIA, memoria);
        renderMemoria();
        return true;
    }

    function borrarMemoria(idx) {
        memoria.splice(idx, 1);
        guardarLS(LS_MEMORIA, memoria);
        renderMemoria();
    }

    function renderMemoria() {
        elMemCount.textContent = memoria.length;
        elMemCount.style.display = memoria.length ? '' : 'none';

        if (!memoria.length) {
            elMemList.innerHTML = '<li class="elipse-mem__empty">Todavía no recuerdo nada.</li>';
            return;
        }
        elMemList.innerHTML = memoria.map((m, i) =>
            '<li><span>' + esc(m.texto) + '</span>' +
            '<button type="button" class="elipse-mem__del" data-i="' + i + '" ' +
            'aria-label="Olvidar">✕</button></li>'
        ).join('');
    }

    elMemList.addEventListener('click', (e) => {
        const btn = e.target.closest('.elipse-mem__del');
        if (btn) borrarMemoria(Number(btn.dataset.i));
    });

    $('elipseMemBtn').addEventListener('click', (e) => {
        e.stopPropagation();
        elMemPanel.classList.toggle('is-open');
    });

    // Click fuera cierra el panel.
    document.addEventListener('click', (e) => {
        if (!elMemPanel.classList.contains('is-open')) return;
        if (!elMemPanel.contains(e.target)) elMemPanel.classList.remove('is-open');
    });

    // ─────────────────────────────────────────────────────────
    // Memoria: historial de la conversacion
    // ─────────────────────────────────────────────────────────

    function guardarHistorial() {
        if (historial.length > MAX_HISTORIAL) historial = historial.slice(-MAX_HISTORIAL);
        guardarLS(LS_HISTORIAL, historial);
    }

    /* Repinta la conversacion anterior sin animarla: ya "estaba ahi", no tiene
       sentido que se escriba de nuevo cada vez que recargas. */
    function restaurarHistorial() {
        if (!historial.length) return;
        quitarBienvenida();

        const sep = document.createElement('div');
        sep.className = 'elipse-sep';
        sep.textContent = 'conversación anterior';
        elMensajes.appendChild(sep);

        historial.forEach((m) => {
            if (m.role === 'user') {
                addMsg('user', esc(m.content), true);
            } else {
                addMsg('ai', m.html || esc(m.content), true);
            }
        });
        bajar(true);
    }

    function nuevaConversacion() {
        historial = [];
        guardarLS(LS_HISTORIAL, historial);
        elMensajes.innerHTML =
            '<div class="elipse-welcome" id="elipseWelcome">' +
            '<div class="elipse-welcome__orb">⚡</div>' +
            '<h2>Hola, soy <em>Elipse</em></h2>' +
            '<p>Tu asistente de IA para OperaCore. Pregúntame sobre máquinas, fallas, ' +
            'órdenes, inventario y trabajadores.</p>' +
            '<div class="elipse-chips-wrap" id="elipseChipsInicio"></div>' +
            '</div>';
        renderChipsInicio();
        elInput.focus();
    }

    $('elipseNuevaBtn').addEventListener('click', nuevaConversacion);

    // ─────────────────────────────────────────────────────────
    // Chips de sugerencias
    // ─────────────────────────────────────────────────────────

    let sugerencias = [];

    function chipsHTML(lista) {
        const grupos = {};
        lista.forEach((p) => { (grupos[p.cat] || (grupos[p.cat] = [])).push(p); });

        let n = 0;
        return Object.keys(grupos).map((cat) => {
            const items = grupos[cat].map((p) =>
                '<button type="button" class="elipse-chip" style="--i:' + (n++) + '" ' +
                'data-q="' + esc(p.q) + '">' + p.icon + ' ' + esc(p.label) + '</button>'
            ).join('');
            return '<div class="elipse-chip-group">' +
                   '<span class="elipse-chip-cat">' + esc(cat) + '</span>' + items + '</div>';
        }).join('');
    }

    function renderChipsInicio() {
        const cont = $('elipseChipsInicio');
        if (cont && sugerencias.length) cont.innerHTML = chipsHTML(sugerencias);
    }

    /* Las sugerencias las define el api (PREGUNTAS_RAPIDAS en
       api/apps/elipse/views.py) y se piden una vez al cargar, para no tener
       la misma lista duplicada en Python y en JS. */
    async function cargarSugerencias() {
        try {
            const res = await fetch(cfg.urlSugerencias);
            const data = await res.json();
            sugerencias = data.sugerencias || [];
            renderChipsInicio();
        } catch (e) {
            /* Sin sugerencias se puede escribir igual; no vale la pena avisar. */
        }
    }

    // Delegacion: cubre los chips de inicio y los que vienen dentro de una
    // respuesta del api (modo offline).
    elMensajes.addEventListener('click', (e) => {
        const chip = e.target.closest('.elipse-chip');
        if (chip && chip.dataset.q) enviar(chip.dataset.q);
    });

    // ─────────────────────────────────────────────────────────
    // Envio
    // ─────────────────────────────────────────────────────────

    function autoAlto() {
        elInput.style.height = 'auto';
        elInput.style.height = Math.min(elInput.scrollHeight, 152) + 'px';
    }
    elInput.addEventListener('input', autoAlto);

    async function enviar(textoDirecto, textoMostrar) {
        if (ocupado) return;
        const txt = (textoDirecto !== undefined ? textoDirecto : elInput.value).trim();
        if (!txt) return;

        if (textoDirecto === undefined) {
            elInput.value = '';
            autoAlto();
        }

        addMsg('user', esc(textoMostrar || txt), false);
        bajar(true);

        // "recuerda que ..." se resuelve aqui: no gastamos una llamada a la IA
        // para algo que es puramente local.
        const recordar = detectarRecuerda(txt);
        if (recordar) {
            const nuevo = agregarMemoria(recordar);
            addMsg('ai', nuevo
                ? '<p>🧠 Anotado: <strong>' + esc(recordar) + '</strong>. Lo tendré presente.</p>'
                : '<p>🧠 Eso ya lo tenía anotado.</p>', false);
            toast(nuevo ? '🧠 Anotado.' : '🧠 Ya lo recordaba.');
            historial.push({ role: 'user', content: txt });
            guardarHistorial();
            return;
        }

        ocupado = true;
        elSend.disabled = true;
        const pensando = mostrarPensando();

        try {
            const res = await fetch(cfg.urlChat, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': cfg.csrf },
                body: JSON.stringify({
                    pregunta: txt,
                    historial: historial.slice(-6).map((m) => ({ role: m.role, content: m.content })),
                    memoria: memoria.map((m) => m.texto),
                }),
            });
            const data = await res.json();

            if (data.error) {
                pensando.limpiar();
                pensando.burbuja.innerHTML =
                    '<span class="elipse-error">⚠ ' + esc(data.error) + '</span>';
                bajar();
            } else {
                pensando.limpiar();
                await escribirHTML(pensando.burbuja, data.html);

                historial.push({ role: 'user', content: txt });
                historial.push({
                    role: 'assistant',
                    content: data.html.replace(/<[^>]+>/g, ' ').slice(0, 800),
                    html: data.html,
                });
                guardarHistorial();
            }
        } catch (e) {
            pensando.limpiar();
            pensando.burbuja.innerHTML =
                '<span class="elipse-error">⚠ Error de conexión.</span>';
            bajar();
        } finally {
            ocupado = false;
            elSend.disabled = false;
            elInput.focus();
        }
    }

    elInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            enviar();
        }
    });
    elSend.addEventListener('click', () => enviar());

    // ── adjuntar reporte de falla en Word o PDF ───────────────────
    if (elAdjuntarBtn && elAdjuntarInput) {
        elAdjuntarInput.addEventListener("change", () => {
            const archivo = elAdjuntarInput.files[0];
            elAdjuntarInput.value = "";
            if (!archivo || ocupado) return;
            if (!window.extraerTextoDocumento) {
                addMsg("ai", "<p>La importación de documentos no está disponible en este momento.</p>", false);
                bajar(true);
                return;
            }

            window.extraerTextoDocumento(archivo)
                .then((textoCrudo) => {
                    const texto = (textoCrudo || "").trim();
                    if (!texto) {
                        addMsg("ai", "<p>No encontré texto en ese documento. Si es un PDF escaneado, usa el Word original o un PDF exportado desde Word.</p>", false);
                        bajar(true);
                        return;
                    }
                    const prompt = "Aquí está un reporte de falla que alguien llenó en Word, " +
                        "ayúdame a levantarlo en el sistema:\n\n" + texto;
                    enviar(prompt, "📄 " + archivo.name);
                })
                .catch(() => {
                    addMsg("ai", "<p>No pude leer ese archivo. Usa un .docx o un PDF que contenga texto seleccionable.</p>", false);
                    bajar(true);
                });
        });
    }

    // ─────────────────────────────────────────────────────────
    // Arranque
    // ─────────────────────────────────────────────────────────

    historial = leerLS(LS_HISTORIAL, []);
    memoria   = leerLS(LS_MEMORIA, []);

    renderMemoria();
    restaurarHistorial();
    cargarSugerencias();
    elInput.focus();
})();
