/* ==========================================================================
   Elipse — chat de "ayudame a redactar" en el formulario de Nueva orden de
   mantenimiento. Mismo patron que fallas/js/elipse-falla.js: el usuario
   platica con Elipse en un panel lateral, y turno a turno la IA va
   rellenando los campos del formulario que ya esta en la pagina. Este
   script solo escribe en los <input>/<select>/<textarea> del DOM -- nunca
   manda nada a la BD. El usuario sigue siendo quien revisa y da "Crear".

   Tambien atiende el caso de llegar aqui desde el chat general de Elipse,
   con los campos ya propuestos en la URL (?elipse=<base64 json>): en ese
   caso ademas hay que abrir el modal de "Nueva orden", que aqui vive
   cerrado por default (a diferencia del formulario de falla, que es una
   pagina aparte).
   ========================================================================== */
(function () {
  "use strict";

  var cfg = window.ELIPSE_ORDEN_CONFIG || {};

  var btnOpen = document.getElementById("btnElipseOrden");
  var panel = document.getElementById("elipseOrdenPanel");
  var btnClose = document.getElementById("elipseOrdenClose");
  var input = document.getElementById("elipseOrdenInput");
  var btnEnviar = document.getElementById("elipseOrdenBtn");
  var chatEl = document.getElementById("elipseOrdenChat");
  var modalOrden = document.getElementById("newOrdenModal");

  function leerJson(id) {
    var el = document.getElementById(id);
    if (!el) return [];
    try {
      var data = JSON.parse(el.textContent || "[]");
      return Array.isArray(data) ? data : [];
    } catch (e) { return []; }
  }

  // Reusamos los mismos json_script ya presentes en la pagina: no tiene
  // caso duplicar el catalogo de maquinas solo para Elipse.
  var maquinas = leerJson("maquinas-data");
  var tiposMantenimiento = leerJson("elipseTiposMantenimientoData");
  var historial = [];
  var camposAcumulados = {};

  function fusionarCampos(campos) {
    campos = campos || {};
    Object.keys(campos).forEach(function (k) {
      var v = campos[k];
      if (v !== null && v !== undefined && v !== "") camposAcumulados[k] = v;
    });
  }

  var ETIQUETAS_CAMPO = {
    descripcion: "Descripción", maquina: "Máquina",
    tipo_mantenimiento: "Tipo", fechaprogramada: "Fecha programada",
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
    // modelo propuso un codigo que no esta en el catalogo (o que el
    // formulario no ofrece, como PREDI/EMER que "oTipo" no lista), preferimos
    // dejar el campo como estaba antes que romper el formulario.
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
    if (set("oDescripcion", campos.descripcion)) aplicados.push("Descripción");
    if (campos.maquina && set("oMaquina", String(campos.maquina))) aplicados.push("Máquina");
    if (campos.tipo_mantenimiento && set("oTipo", String(campos.tipo_mantenimiento))) aplicados.push("Tipo");
    if (set("oFecha", campos.fechaprogramada)) aplicados.push("Fecha programada");
    return aplicados;
  }

  function abrirModalOrden() {
    if (modalOrden && !modalOrden.open) modalOrden.showModal();
  }

  // ── llegar aqui ya autocompletado desde el chat general de Elipse ──────
  // Va antes del early return del panel: el prellenado por URL debe abrir
  // el modal y aplicar los campos aunque el panel lateral no exista en la
  // pagina (p.ej. si el usuario es tecnico y no tiene "Nueva orden").
  (function prellenarDesdeURL() {
    var params = new URLSearchParams(window.location.search);
    var b64 = params.get("elipse");
    if (!b64) return;
    try {
      var bin = atob(b64.replace(/-/g, "+").replace(/_/g, "/"));
      var bytes = Uint8Array.from(bin, function (c) { return c.charCodeAt(0); });
      var json = new TextDecoder("utf-8").decode(bytes);
      var campos = JSON.parse(json);
      abrirModalOrden();
      aplicarCampos(campos);
      window.history.replaceState({}, "", window.location.pathname);
    } catch (e) { /* link corrupto, se ignora */ }
  })();

  if (!btnOpen || !panel) return;

  // ── abrir / cerrar ──────────────────────────────────────
  // El panel vive DENTRO de <dialog id="newOrdenModal"> (ver index.html),
  // como hermano de <form>, con su propio CSS para abrirse "junto" al
  // formulario en vez de superponerse. Asi evitamos el problema de que un
  // <aside> normal quede atrapado detras del "top layer" del <dialog>
  // (mismo caso que resolvieron para oReporteFallaVer mas arriba, pero aqui
  // ni siquiera hace falta cerrar el modal: ambos comparten el top layer
  // porque el panel esta anidado adentro).
  function abrirPanel() {
    panel.classList.add("is-open");
    panel.setAttribute("aria-hidden", "false");
    if (chatEl && !chatEl.children.length) {
      pintarMsg("ai", "¡Hola! Cuéntame qué necesita la máquina y te ayudo a llenar la orden.");
    }
    setTimeout(function () { if (input) input.focus(); }, 60);
  }

  function cerrarPanel() {
    panel.classList.remove("is-open");
    panel.setAttribute("aria-hidden", "true");
  }

  btnOpen.addEventListener("click", function (ev) {
    ev.preventDefault();
    abrirPanel();
  });
  if (btnClose) btnClose.addEventListener("click", cerrarPanel);
  // Nota: ya no hay overlay propio que cerrar con clic-afuera; el <dialog>
  // padre ya tiene su ::backdrop, y Escape sigue cerrando el panel primero.
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

    var historialParaEnviar = historial.slice(-20);
    var resumen = resumenCamposTexto();
    if (resumen) historialParaEnviar = historialParaEnviar.concat([{ role: "assistant", content: resumen }]);

    fetch(cfg.urlAutocompletar, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": cfg.csrf || "" },
      body: JSON.stringify({
        texto: texto,
        maquinas: maquinas,
        tipos_mantenimiento: tiposMantenimiento,
        historial: historialParaEnviar,
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

        var faltantes = ["descripcion", "maquina", "tipo_mantenimiento"]
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
