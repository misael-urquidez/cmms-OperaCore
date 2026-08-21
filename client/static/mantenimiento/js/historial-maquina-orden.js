(function () {
  "use strict";

  var root = document.querySelector(".ordenes");
  var URL_TPL = root ? root.dataset.historialMaquinaUrlBase : null;

  var btn = document.getElementById("btnHistorialOrden");
  var maquinaSel = document.getElementById("oMaquina");
  var panel = document.getElementById("historialOrdenMaquina");
  var btnClose = document.getElementById("historialOrdenClose");
  var lista = document.getElementById("historialOrdenLista");

  if (!btn || !maquinaSel || !panel || !URL_TPL) return;

  var MAX_COMPACTO = 3;
  var ultimoCodigo = null;
  var historialActual = [];
  var expandido = false;

  function urlPara(codigo) {
    return URL_TPL.replace("CODIGOPLACEHOLDER", encodeURIComponent(codigo));
  }

  function badgeTipo(tipo) {
    var t = (tipo || "").toString().toUpperCase();
    var span = document.createElement("span");
    span.className = "historial-maquina__badge historial-maquina__badge--" + (t === "FALLA" ? "FALLA" : "ORDEN");
    span.textContent = t || "—";
    return span;
  }

  function badgeEstado(codigo, texto) {
    var c = (codigo || "").toString().toUpperCase();
    var span = document.createElement("span");
    span.className = "historial-maquina__estado historial-maquina__estado--" + (c || "SOLIC");
    span.textContent = texto || c || "—";
    return span;
  }

  function renderItem(h) {
    var item = document.createElement("div");
    item.className = "historial-maquina__item";

    var top = document.createElement("div");
    top.className = "historial-maquina__item-top";
    top.appendChild(badgeTipo(h.tipo));
    var fecha = document.createElement("span");
    fecha.className = "historial-maquina__fecha";
    fecha.textContent = h.fecha || "";
    top.appendChild(fecha);
    item.appendChild(top);

    var detalle = document.createElement("p");
    detalle.className = "historial-maquina__detalle";
    detalle.textContent = h.detalle || "";
    item.appendChild(detalle);

    var bottom = document.createElement("div");
    bottom.className = "historial-maquina__item-bottom";
    bottom.appendChild(badgeEstado(h.estado, h.estado_nombre));
    var trabajador = document.createElement("span");
    trabajador.className = "historial-maquina__trabajador";
    trabajador.textContent = h.trabajador_nombre || "—";
    bottom.appendChild(trabajador);
    item.appendChild(bottom);

    return item;
  }

  // ── pinta la lista según el estado compacto/expandido, y agrega el
  // boton "Ver más" / "Ver menos" cuando hay mas de MAX_COMPACTO filas ──
  function render(historial) {
    historialActual = historial || [];
    lista.innerHTML = "";

    if (historialActual.length === 0) {
      var vacio = document.createElement("p");
      vacio.className = "historial-maquina__vacio";
      vacio.textContent = "Sin historial previo para esta máquina.";
      lista.appendChild(vacio);
      return;
    }

    var limite = expandido ? historialActual.length : MAX_COMPACTO;
    historialActual.slice(0, limite).forEach(function (h) {
      lista.appendChild(renderItem(h));
    });

    if (historialActual.length > MAX_COMPACTO) {
      var boton = document.createElement("button");
      boton.type = "button";
      boton.className = "historial-maquina__vermas";
      boton.textContent = expandido
        ? "Ver menos"
        : "Ver más (" + (historialActual.length - MAX_COMPACTO) + ")";
      boton.addEventListener("click", function () {
        expandido = !expandido;
        panel.classList.toggle("is-expanded", expandido);
        render(historialActual);
      });
      lista.appendChild(boton);
    }
  }

  function cargar(codigo) {
    if (!codigo) {
      lista.innerHTML = '<p class="historial-maquina__vacio">Selecciona primero una máquina.</p>';
      return;
    }
    if (codigo === ultimoCodigo) return;
    ultimoCodigo = codigo;
    lista.innerHTML = '<p class="historial-maquina__cargando">Cargando historial…</p>';

    fetch(urlPara(codigo))
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (codigo !== maquinaSel.value) return; // el usuario ya cambió de máquina
        expandido = false;
        panel.classList.remove("is-expanded");
        render(data.historial);
      })
      .catch(function () {
        lista.innerHTML = '<p class="historial-maquina__vacio">No se pudo cargar el historial.</p>';
      });
  }

  // ── abrir / cerrar, mismo patrón que el panel de Elipse: aside embebido
  // junto al form, animando su width, en vez del <div hidden> de antes ──
  function abrirPanel() {
    panel.classList.add("is-open");
    panel.setAttribute("aria-hidden", "false");
    document.dispatchEvent(new CustomEvent("orden-panel:open", { detail: { panel: "historial" } }));
    cargar(maquinaSel.value);
  }

  function cerrarPanel() {
    panel.classList.remove("is-open");
    panel.setAttribute("aria-hidden", "true");
  }

  btn.addEventListener("click", function () {
    if (panel.classList.contains("is-open")) {
      cerrarPanel();
    } else {
      abrirPanel();
    }
  });

  if (btnClose) btnClose.addEventListener("click", cerrarPanel);

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && panel.classList.contains("is-open")) cerrarPanel();
  });

  // Si se abre el panel de Elipse, este se cierra (y viceversa, ver el
  // listener agregado en elipse-mantenimiento.js): no caben los dos abiertos
  // a la vez a gusto.
  document.addEventListener("orden-panel:open", function (e) {
    if (e.detail && e.detail.panel !== "historial" && panel.classList.contains("is-open")) {
      cerrarPanel();
    }
  });

  maquinaSel.addEventListener("change", function () {
    ultimoCodigo = null;
    if (panel.classList.contains("is-open")) cargar(maquinaSel.value);
  });

  var modal = document.getElementById("newOrdenModal");
  if (modal) {
    modal.addEventListener("close", function () {
      cerrarPanel();
      ultimoCodigo = null;
    });
  }
})();