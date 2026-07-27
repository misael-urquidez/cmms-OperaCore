/* ==========================================================================
   Elipse — chat de "ayudame a redactar" en el reporte de falla.

   El tecnico platica con Elipse en un panel lateral: describe la falla, y
   turno a turno la IA va preguntando lo que falta y rellenando los campos
   del formulario que ya esta en la pagina. Este script solo escribe en los
   <input>/<select>/<textarea> del DOM -- nunca manda nada a la BD. El
   tecnico sigue siendo quien revisa y da "Reportar falla".

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
  var historial = [];

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
      aplicarCampos(JSON.parse(json));
      window.history.replaceState({}, "", window.location.pathname);
    } catch (e) { /* link corrupto, se ignora */ }
  })();

  if (!btnOpen || !panel || !overlay) return;

  // ── abrir / cerrar ──────────────────────────────────────
  function abrirPanel() {
    panel.classList.add("is-open");
    panel.setAttribute("aria-hidden", "false");
    overlay.hidden = false;
    document.body.style.overflow = "hidden";
    if (chatEl && !chatEl.children.length) {
      pintarMsg("ai", "¡Hola! Cuéntame qué pasó con la máquina y te ayudo a llenar el reporte.");
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

  // ── burbujas del chat ───────────────────────────────────
  function pintarMsg(rol, texto, extraHTML) {
    if (!chatEl) return;
    var d = document.createElement("div");
    d.className = "elipse-falla-panel__msg elipse-falla-panel__msg--" + (rol === "user" ? "user" : "ai");
    d.textContent = texto;  // textContent, no innerHTML: el texto viene del modelo
    if (extraHTML) d.insertAdjacentHTML("beforeend", extraHTML);
    chatEl.appendChild(d);
    chatEl.scrollTop = chatEl.scrollHeight;
  }

  // ── un turno de conversacion ────────────────────────────
  function enviarTurno() {
    var texto = (input && input.value ? input.value : "").trim();
    if (!texto || !cfg.urlAutocompletar) return;

    pintarMsg("user", texto);
    historial.push({ role: "user", content: texto });
    input.value = "";
    btnEnviar.disabled = true;

    fetch(cfg.urlAutocompletar, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": cfg.csrf || "" },
      body: JSON.stringify({
        texto: texto,
        maquinas: maquinas,
        severidades: severidades,
        tipos_falla: tiposFalla,
        historial: historial.slice(-6),
      }),
    })
      .then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
      .then(function (res) {
        if (!res.ok || res.data.error) {
          pintarMsg("ai", res.data.error || "No se pudo procesar la descripción.");
          return;
        }
        var aplicados = aplicarCampos(res.data.campos);
        var nota = aplicados.length
          ? "<ul>" + aplicados.map(function (a) { return "<li>" + a + "</li>"; }).join("") + "</ul>"
          : "";
        pintarMsg("ai", res.data.mensaje || "Listo, revisa el formulario.", nota);
        historial.push({ role: "assistant", content: res.data.mensaje || "" });
      })
      .catch(function () {
        pintarMsg("ai", "No fue posible conectar con Elipse. Intenta llenar el formulario a mano.");
      })
      .then(function () { btnEnviar.disabled = false; });
  }

  if (btnEnviar) btnEnviar.addEventListener("click", enviarTurno);
  if (input) {
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); enviarTurno(); }
    });
  }
})();
