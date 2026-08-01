/* ==========================================================================
   Elipse — panel de "ayudame a redactar / diagnosticar" en el reporte de
   falla, con DOS modos:

   - "redactar": el tecnico platica que paso y, turno a turno, Elipse va
     llenando TODOS los campos del formulario (asunto, descripcion, causa
     raiz, tiempos, maquina, severidad, tipo de falla, estado...).

   - "diagnosticar": cumple especificamente el RNF de "Asistencia
     Inteligente para Diagnostico de Fallas": el tecnico describe el
     sintoma, Elipse compara contra el HISTORIAL REAL de esa maquina y
     propone una causa probable + severidad recomendada, con un boton para
     aplicarla al formulario. El tecnico puede aceptarla o ignorarla.

   En ambos modos este script SOLO escribe en los <input>/<select>/
   <textarea> del DOM -- nunca manda nada a la BD. El tecnico sigue siendo
   quien revisa y da "Reportar falla".

   Tambien atiende el caso de llegar aqui desde el chat general de Elipse,
   con los campos ya propuestos en la URL (?elipse=<base64 json>).
   ========================================================================== */
(function () {
  "use strict";

  var cfg = window.ELIPSE_FALLA_CONFIG || {};

  var btnOpen = document.getElementById("btnElipseFalla");
  var panel = document.getElementById("elipseFallaPanel");
  var overlay = document.getElementById("elipseFallaOverlay");
  var btnClose = document.getElementById("elipseFallaClose");
  var input = document.getElementById("elipseFallaInput");
  var btnEnviar = document.getElementById("elipseFallaBtn");
  var chatEl = document.getElementById("elipseFallaChat");
  var hintEl = document.getElementById("elipseFallaHint");
  var tabRedactar = document.getElementById("elipseTabRedactar");
  var tabDiagnosticar = document.getElementById("elipseTabDiagnosticar");

  function leerJson(id) {
    var el = document.getElementById(id);
    if (!el) return [];
    try {
      var data = JSON.parse(el.textContent || "[]");
      return Array.isArray(data) ? data : [];
    } catch (e) { return []; }
  }

  var maquinas = leerJson("elipseMaquinasData");
  var severidades = leerJson("elipseSeveridadesData");
  var tiposFalla = leerJson("elipseTiposFallaData");
  var estados = leerJson("elipseEstadosData");

  function escaparHTML(s) {
    var d = document.createElement("div");
    d.textContent = s === null || s === undefined ? "" : String(s);
    return d.innerHTML;
  }

  function nombrePorCodigo(lista, codigo) {
    for (var i = 0; i < (lista || []).length; i++) {
      if (lista[i] && String(lista[i].codigo) === String(codigo)) return lista[i].nombre;
    }
    return codigo;
  }

  // ── modo activo: "redactar" | "diagnosticar" ────────────
  var modoActual = "redactar";

  var TEXTOS_MODO = {
    redactar: {
      hint: "Cuéntame qué pasó con la máquina. Voy preguntando lo que falte (severidad, estado, fecha…) y lleno el formulario contigo.",
      intro: "¡Hola! Cuéntame qué pasó con la máquina y te ayudo a llenar el reporte.",
      placeholder: "Ej. la banda del pick and place se trabó, lleva 2 horas parada...",
    },
    diagnosticar: {
      hint: "Dime en qué máquina y qué síntomas está presentando. Comparo contra el historial de fallas de esa máquina y te propongo una causa probable y la severidad recomendada — tú decides si la usas.",
      intro: "¡Hola! Dime la máquina y los síntomas que está presentando (o selecciona la máquina en el formulario) y te doy un diagnóstico probable basado en fallas anteriores.",
      placeholder: "Ej. MAQ003 hace un ruido metálico y vibra más de lo normal...",
    },
  };

  // ── estado propio de cada modo ───────────────────────────
  var historialRedactar = [];
  var camposAcumulados = {};

  var diagMaquina = null;
  var diagSintomas = [];
  var diagUltimaSugerencia = null;

  function fusionarCampos(campos) {
    campos = campos || {};
    Object.keys(campos).forEach(function (k) {
      var v = campos[k];
      if (v !== null && v !== undefined && v !== "") camposAcumulados[k] = v;
    });
  }

  var ETIQUETAS_CAMPO = {
    asunto: "Asunto", descripcion: "Descripción", causaRaiz: "Causa raíz",
    tiempoParo: "Tiempo de paro", fecha: "Fecha", maquina: "Máquina",
    tipo_severidad: "Severidad", tipo_falla: "Tipo de falla",
    estado_reporte: "Estado del reporte",
  };

  function resumenCamposTexto() {
    var partes = Object.keys(camposAcumulados).map(function (k) {
      return (ETIQUETAS_CAMPO[k] || k) + "=" + camposAcumulados[k];
    });
    return partes.length ? "Datos ya confirmados hasta ahora: " + partes.join(", ") + "." : "";
  }

  // ── rellenar un campo del formulario, con destello visual ──
  function set(id, val) {
    var el = document.getElementById(id);
    if (!el || val === null || val === undefined || val === "") return false;

    // En un <select> solo aceptamos un valor que exista como <option>: si el
    // modelo propuso un codigo que no esta en el catalogo, preferimos dejar
    // el campo como estaba antes que romper el formulario.
    if (el.tagName === "SELECT") {
      var existe = Array.prototype.some.call(el.options, function (o) {
        return o.value === String(val);
      });
      if (!existe) return false;
    }

    el.value = val;
    el.classList.remove("elipse-filled");
    void el.offsetWidth;  // reflow, para poder re-disparar la animacion
    el.classList.add("elipse-filled");
    return true;
  }

  function aplicarCampos(campos) {
    campos = campos || {};
    var aplicados = [];
    if (set("asunto", campos.asunto)) aplicados.push("Asunto");
    if (set("descripcion", campos.descripcion)) aplicados.push("Descripción");
    if (set("causaRaiz", campos.causaRaiz)) aplicados.push("Causa raíz");
    if (campos.tiempoParo !== null && campos.tiempoParo !== undefined && campos.tiempoParo !== "") {
      if (set("tiempoParo", campos.tiempoParo)) aplicados.push("Tiempo de paro");
    }
    if (set("fechaSolucion", campos.fecha)) aplicados.push("Fecha");
    if (campos.maquina && set("maquina", String(campos.maquina))) aplicados.push("Máquina");
    if (campos.tipo_severidad && set("tipo_severidad", String(campos.tipo_severidad))) aplicados.push("Severidad");
    if (campos.tipo_falla !== null && campos.tipo_falla !== undefined && campos.tipo_falla !== "") {
      if (set("tipo_falla", String(campos.tipo_falla))) aplicados.push("Tipo de falla");
    }
    if (campos.estado_reporte && set("estado_reporte", String(campos.estado_reporte))) aplicados.push("Estado del reporte");
    return aplicados;
  }

  // ── llegar aqui ya autocompletado desde el chat general de Elipse ──────
  // Va antes del early return del panel: el prellenado por URL debe funcionar
  // aunque el panel no exista en la pagina.
  (function prellenarDesdeURL() {
    var params = new URLSearchParams(window.location.search);
    var b64 = params.get("elipse");
    if (!b64) return;
    try {
      var bin = atob(b64.replace(/-/g, "+").replace(/_/g, "/"));
      var bytes = Uint8Array.from(bin, function (c) { return c.charCodeAt(0); });
      var json = new TextDecoder("utf-8").decode(bytes);
      var campos = JSON.parse(json);
      aplicarCampos(campos);
      fusionarCampos(campos);
      window.history.replaceState({}, "", window.location.pathname);
    } catch (e) { /* link corrupto, se ignora */ }
  })();

  if (!btnOpen || !panel || !overlay) return;

  // ── burbujas del chat (definida antes de cambiarModo/abrirPanel) ───────
  function pintarMsg(rol, texto, extraHTML) {
    if (!chatEl) return;
    var d = document.createElement("div");
    d.className = "elipse-falla-panel__msg elipse-falla-panel__msg--" + (rol === "user" ? "user" : "ai");
    d.textContent = texto;  // textContent, no innerHTML: el texto viene del modelo
    if (extraHTML) d.insertAdjacentHTML("beforeend", extraHTML);
    chatEl.appendChild(d);
    chatEl.scrollTop = chatEl.scrollHeight;
  }

  // ── cambiar entre "Redactar" y "Diagnosticar" ───────────
  function cambiarModo(modo) {
    if (!TEXTOS_MODO[modo] || modo === modoActual) return;
    modoActual = modo;
    if (tabRedactar) {
      tabRedactar.classList.toggle("is-active", modo === "redactar");
      tabRedactar.setAttribute("aria-selected", modo === "redactar" ? "true" : "false");
    }
    if (tabDiagnosticar) {
      tabDiagnosticar.classList.toggle("is-active", modo === "diagnosticar");
      tabDiagnosticar.setAttribute("aria-selected", modo === "diagnosticar" ? "true" : "false");
    }
    if (hintEl) hintEl.textContent = TEXTOS_MODO[modo].hint;
    if (input) input.placeholder = TEXTOS_MODO[modo].placeholder;
    if (chatEl) chatEl.innerHTML = "";
    pintarMsg("ai", TEXTOS_MODO[modo].intro);
  }

  if (tabRedactar) tabRedactar.addEventListener("click", function () { cambiarModo("redactar"); });
  if (tabDiagnosticar) tabDiagnosticar.addEventListener("click", function () { cambiarModo("diagnosticar"); });

  // ── abrir / cerrar ──────────────────────────────────────
  function abrirPanel() {
    panel.classList.add("is-open");
    panel.setAttribute("aria-hidden", "false");
    overlay.hidden = false;
    document.body.style.overflow = "hidden";
    if (chatEl && !chatEl.children.length) {
      pintarMsg("ai", TEXTOS_MODO[modoActual].intro);
    }
    setTimeout(function () { if (input) input.focus(); }, 60);
  }

  function cerrarPanel() {
    panel.classList.remove("is-open");
    panel.setAttribute("aria-hidden", "true");
    overlay.hidden = true;
    document.body.style.overflow = "";
  }

  btnOpen.addEventListener("click", abrirPanel);
  if (btnClose) btnClose.addEventListener("click", cerrarPanel);
  overlay.addEventListener("click", cerrarPanel);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && panel.classList.contains("is-open")) cerrarPanel();
  });

  // ── MODO "redactar": un turno de conversacion que llena el formulario ──
  function turnoRedactar(texto) {
    if (!cfg.urlAutocompletar) return Promise.resolve();

    historialRedactar.push({ role: "user", content: texto });

    // Ventana de historial mas amplia y recordatorio explicito de los
    // datos confirmados, para conservar el contexto si se trunca el chat.
    var historialParaEnviar = historialRedactar.slice(-20);
    var resumen = resumenCamposTexto();
    if (resumen) historialParaEnviar = historialParaEnviar.concat([{ role: "assistant", content: resumen }]);

    return fetch(cfg.urlAutocompletar, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": cfg.csrf || "" },
      body: JSON.stringify({
        texto: texto,
        maquinas: maquinas,
        severidades: severidades,
        tipos_falla: tiposFalla,
        estados: estados,
        historial: historialParaEnviar,
        campos_previos: camposAcumulados,
      }),
    })
      .then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
      .then(function (res) {
        if (!res.ok || res.data.error) {
          pintarMsg("ai", res.data.error || "No se pudo procesar la descripción.");
          return;
        }
        aplicarCampos(res.data.campos);
        fusionarCampos(res.data.campos);

        var faltantes = ["asunto", "fecha", "maquina", "tipo_severidad", "tipo_falla", "estado_reporte"]
          .filter(function (k) { return !camposAcumulados[k]; });

        var nota = Object.keys(camposAcumulados).length
          ? "<p style='margin:6px 0 2px;font-size:11px;color:var(--color-muted,#94a3b8)'>Confirmado:</p><ul>" +
            Object.keys(camposAcumulados).map(function (k) { return "<li>" + (ETIQUETAS_CAMPO[k] || k) + "</li>"; }).join("") +
            "</ul>" +
            (faltantes.length
              ? "<p style='margin:2px 0 0;font-size:11px;color:var(--color-muted,#94a3b8)'>Falta: " +
                faltantes.map(function (k) { return ETIQUETAS_CAMPO[k] || k; }).join(", ") + "</p>"
              : "")
          : "";

        pintarMsg("ai", res.data.mensaje || "Listo, revisa el formulario.", nota);
        historialRedactar.push({ role: "assistant", content: res.data.mensaje || "" });
      })
      .catch(function () {
        pintarMsg("ai", "No fue posible conectar con Elipse. Intenta llenar el formulario a mano.");
      });
  }

  // ── MODO "diagnosticar": cumple el RNF, causa probable + severidad ─────
  function detectarMaquinaEnTexto(texto) {
    var t = (texto || "").toLowerCase();
    for (var i = 0; i < maquinas.length; i++) {
      var m = maquinas[i];
      if (!m) continue;
      var nombre = String(m.nombre || "").toLowerCase();
      var codigo = String(m.codigo || "").toLowerCase();
      if ((nombre && t.indexOf(nombre) !== -1) || (codigo && t.indexOf(codigo) !== -1)) {
        return m;
      }
    }
    return null;
  }

  var ETIQUETAS_FUENTE_DIAG = {
    ia: "Sugerido por Elipse (IA)",
    historial_local: "Sin conexión — basado en el historial de esta máquina",
    consejo_general: "Consejo general — esta máquina no tiene historial aún",
  };

  function turnoDiagnosticar(texto) {
    if (!cfg.urlDiagnostico) {
      pintarMsg("ai", "El diagnóstico automático no está disponible en este momento.");
      return Promise.resolve();
    }

    // 1) resolver la maquina: primero la ya seleccionada en el formulario,
    //    luego lo que el tecnico haya escrito.
    if (!diagMaquina) {
      var selMaquina = document.getElementById("maquina");
      if (selMaquina && selMaquina.value) {
        diagMaquina = selMaquina.value;
      } else {
        var detectada = detectarMaquinaEnTexto(texto);
        if (detectada) diagMaquina = detectada.codigo;
      }
    }
    diagSintomas.push(texto);

    if (!diagMaquina) {
      pintarMsg("ai", "¿De qué máquina estamos hablando? Selecciónala en el formulario o dime su nombre/código.");
      return Promise.resolve();
    }

    var sintoma = diagSintomas.join(". ");
    if (sintoma.replace(/\s+/g, "").length < 12) {
      pintarMsg("ai", "Cuéntame un poco más del síntoma (qué hace la máquina, desde cuándo, etc.) para comparar contra su historial.");
      return Promise.resolve();
    }

    return fetch(cfg.urlDiagnostico, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": cfg.csrf || "" },
      body: JSON.stringify({ maquina: diagMaquina, sintoma: sintoma }),
    })
      .then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
      .then(function (res) {
        if (!res.ok || res.data.error) {
          pintarMsg("ai", (res.data && res.data.error) || "No se pudo generar el diagnóstico.");
          return;
        }
        diagUltimaSugerencia = res.data;
        var nombreMaquina = nombrePorCodigo(maquinas, diagMaquina);
        var nombreSeveridad = nombrePorCodigo(severidades, res.data.severidad);
        var etiquetaFuente = ETIQUETAS_FUENTE_DIAG[res.data.fuente] || "";
        var casos = res.data.casos_similares > 0
          ? "Basado en " + res.data.casos_similares + " falla(s) previa(s) de " + escaparHTML(nombreMaquina) + ". "
          : "";

        var extra =
          "<p style='margin:6px 0 2px;font-size:11px;color:var(--color-muted,#94a3b8)'>" + escaparHTML(etiquetaFuente) + "</p>" +
          "<p style='margin:2px 0;font-size:13px'><strong>Causa probable:</strong> " + escaparHTML(res.data.causa_probable || "") + "</p>" +
          "<p style='margin:2px 0;font-size:13px'><strong>Severidad sugerida:</strong> " + escaparHTML(nombreSeveridad || "") + "</p>" +
          (res.data.justificacion ? "<p style='margin:2px 0 8px;font-size:12px;color:var(--color-muted,#94a3b8)'>" + escaparHTML(res.data.justificacion) + "</p>" : "") +
          "<button type='button' class='elipse-diag-usar' id='elipseDiagUsarBtn_" + Date.now() + "'>Usar esta sugerencia</button>";

        pintarMsg("ai", casos + "Esto encontré:", extra);

        var btnUsar = chatEl.querySelector("#elipseDiagUsarBtn_" + Date.now()) || chatEl.lastElementChild.querySelector(".elipse-diag-usar");
        if (btnUsar) {
          btnUsar.addEventListener("click", function () {
            if (!diagUltimaSugerencia) return;
            set("maquina", diagMaquina);
            set("causaRaiz", diagUltimaSugerencia.causa_probable);
            set("tipo_severidad", diagUltimaSugerencia.severidad);
            fusionarCampos({
              maquina: diagMaquina,
              causaRaiz: diagUltimaSugerencia.causa_probable,
              tipo_severidad: diagUltimaSugerencia.severidad,
            });
            btnUsar.disabled = true;
            btnUsar.textContent = "Aplicado ✓";
            pintarMsg("ai", "Listo, apliqué la causa raíz y la severidad al formulario. Sigues pudiendo editarlas a mano si no te parecen.");
          });
        }
      })
      .catch(function () {
        pintarMsg("ai", "No fue posible conectar con Elipse para el diagnóstico.");
      });
  }

  // ── un turno de conversacion (repartido segun el modo activo) ──────────
  function enviarTurno() {
    var texto = (input && input.value ? input.value : "").trim();
    if (!texto) return;

    pintarMsg("user", texto);
    input.value = "";
    btnEnviar.disabled = true;

    var promesa = modoActual === "diagnosticar" ? turnoDiagnosticar(texto) : turnoRedactar(texto);
    promesa.then(function () { btnEnviar.disabled = false; });
  }

  if (btnEnviar) btnEnviar.addEventListener("click", enviarTurno);
  if (input) {
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); enviarTurno(); }
    });
  }

  // ── importar reporte desde un .docx o .pdf con texto (siempre llena el
  //    formulario completo, asi que forzamos el modo "redactar") ─────────
  var btnImportarDocx = document.getElementById("btnImportarDocx");
  var inputImportarDocx = document.getElementById("inputImportarDocx");

  if (btnImportarDocx && inputImportarDocx) {
    inputImportarDocx.addEventListener("change", function () {
      var archivo = inputImportarDocx.files[0];
      inputImportarDocx.value = "";
      if (!archivo) return;
      if (!window.extraerTextoDocumento || !cfg.urlAutocompletar) {
        cambiarModo("redactar");
        abrirPanel();
        pintarMsg("ai", "La importación de documentos no está disponible en este momento.");
        return;
      }

      cambiarModo("redactar");
      abrirPanel();
      pintarMsg("ai", "Leyendo " + archivo.name + "…");

      window.extraerTextoDocumento(archivo)
        .then(function (textoCrudo) {
          var texto = (textoCrudo || "").trim();
          if (!texto) {
            pintarMsg("ai", "No encontré texto en ese documento. Si es un PDF escaneado, expórtalo desde Word o usa el archivo original.");
            return;
          }

          historialRedactar.push({ role: "user", content: texto });
          var resumen = resumenCamposTexto();
          var historialParaEnviar = resumen
            ? historialRedactar.slice(-20).concat([{ role: "assistant", content: resumen }])
            : historialRedactar.slice(-20);

          return fetch(cfg.urlAutocompletar, {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": cfg.csrf || "" },
            body: JSON.stringify({
              texto: texto,
              maquinas: maquinas,
              severidades: severidades,
              tipos_falla: tiposFalla,
              estados: estados,
              historial: historialParaEnviar,
              campos_previos: camposAcumulados,
            }),
          })
            .then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
            .then(function (res) {
              if (!res.ok || res.data.error) {
                pintarMsg("ai", res.data.error || "No se pudo leer el documento.");
                return;
              }
              aplicarCampos(res.data.campos);
              fusionarCampos(res.data.campos);
              pintarMsg("ai", res.data.mensaje || "Listo, importé lo que encontré en el documento. Revisa el formulario.");
              historialRedactar.push({ role: "assistant", content: res.data.mensaje || "" });
            });
        })
        .catch(function () {
          pintarMsg("ai", "No pude leer ese archivo. Usa un .docx o un PDF que contenga texto seleccionable.");
        });
    });
  }
})();