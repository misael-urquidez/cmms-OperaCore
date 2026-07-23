(function () {
  "use strict";

  var root = document.querySelector(".monitoring");
  if (!root) return;

  var DATOS_URL = root.dataset.datosUrl;
  var INDICADORES_TPL = root.dataset.indicadoresUrlBase;
  var HISTORIAL_TPL = root.dataset.historialUrlBase;
  var ESTADO_TPL = root.dataset.estadoUrlBase;
  var CATALOGOS_URL = root.dataset.catalogosUrl;
  var CREAR_URL = root.dataset.crearUrl;
  var MODO_TPL = root.dataset.modoUrlBase;
  var LECTURA_MANUAL_URL = root.dataset.lecturaManualUrl;
  var SIMULAR_TPL = root.dataset.simularUrlBase;
  var REGISTRO_OPS_TPL = root.dataset.registroOpsUrlBase;

  var canvas = document.getElementById("plantCanvas");
  var linksSvg = document.getElementById("plantLinks");
  var emptyMsg = document.getElementById("plantEmpty");
  var refreshStatus = document.getElementById("refreshStatus");

  var STORAGE_KEY = "operacore.monitoreo.layout.v1";
  var NODE_W = 150, NODE_H = 96, GAP_X = 190, GAP_Y = 150, PAD = 40;

  var estado = {
    maquinas: [],       // ultimo snapshot del feed
    posiciones: cargarLayout(),
    seleccionada: null,
  };

  // ---------------------------------------------------------------- utils
  function cargarLayout() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
    } catch (e) { return {}; }
  }
  function guardarLayout() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(estado.posiciones)); } catch (e) {}
  }
  function getCookie(nombre) {
    var valor = null;
    if (document.cookie && document.cookie !== "") {
      document.cookie.split(";").forEach(function (c) {
        c = c.trim();
        if (c.substring(0, nombre.length + 1) === nombre + "=") {
          valor = decodeURIComponent(c.substring(nombre.length + 1));
        }
      });
    }
    return valor;
  }
  function urlPara(tpl, codigo) { return tpl.replace("__CODIGO__", encodeURIComponent(codigo)); }
  function estadoValido(codigo) { return ["OPERA", "MANTE", "FALLO"].indexOf(codigo) !== -1 ? codigo : "sin"; }

  // -------------------------------------------------------- layout inicial
  function posicionPorDefecto(codigo, index, lineaIndex, indexEnLinea) {
    var guardada = estado.posiciones[codigo];
    if (guardada) return guardada;
    return {
      x: PAD + indexEnLinea * GAP_X,
      y: PAD + lineaIndex * GAP_Y,
    };
  }

  // ------------------------------------------------------------- render
  function agruparPorLinea(maquinas) {
    var grupos = {}, orden = [];
    maquinas.forEach(function (m) {
      var clave = m.linea || "Sin línea";
      if (!grupos[clave]) { grupos[clave] = []; orden.push(clave); }
      grupos[clave].push(m);
    });
    return orden.map(function (clave) { return { linea: clave, maquinas: grupos[clave] }; });
  }

  function render(maquinas) {
    estado.maquinas = maquinas;
    emptyMsg.hidden = maquinas.length > 0;

    var grupos = agruparPorLinea(maquinas);
    var maxX = 0, maxY = 0;

    // limpiar nodos previos (dejamos el svg de links y el mensaje vacío)
    Array.prototype.slice.call(canvas.querySelectorAll(".machine-node")).forEach(function (n) { n.remove(); });

    grupos.forEach(function (grupo, gi) {
      grupo.maquinas.forEach(function (m, i) {
        var pos = posicionPorDefecto(m.codigo, 0, gi, i);
        estado.posiciones[m.codigo] = pos;
        maxX = Math.max(maxX, pos.x + NODE_W);
        maxY = Math.max(maxY, pos.y + NODE_H);
        canvas.appendChild(crearNodo(m, pos));
      });
    });

    canvas.style.minWidth = Math.max(maxX + PAD, canvas.parentElement.clientWidth) + "px";
    canvas.style.minHeight = Math.max(maxY + PAD, 560) + "px";

    dibujarConexiones(grupos);
  }

  function crearNodo(m, pos) {
    var node = document.createElement("div");
    node.className = "machine-node";
    node.dataset.codigo = m.codigo;
    node.style.left = pos.x + "px";
    node.style.top = pos.y + "px";

    var estadoClase = estadoValido(m.estado_maquina);
    var ledClase = m.requiere_revision_preventiva ? "ALERT" : estadoClase;

    var vibracion = m.ultima_lectura ? m.ultima_lectura.vibracion : null;
    var umbral = m.umbral_vibracion || 4.0;
    var pct = vibracion !== null ? Math.min(100, Math.round((vibracion / umbral) * 100)) : 0;
    var esAlta = vibracion !== null && vibracion > umbral;

    node.innerHTML =
      '<div class="machine-node__card">' +
        '<div class="machine-node__top"><span class="machine-node__led machine-node__led--' + ledClase + '"></span>' +
        '<span class="machine-node__code">' + m.codigo + '</span></div>' +
        '<span class="machine-node__name">' + m.nombre + '</span>' +
        '<span class="machine-node__line">' + (m.linea || "Sin línea") + " · " + (m.modo_monitoreo || "") + '</span>' +
        '<div class="machine-node__vib">' +
          '<div class="machine-node__vib-track"><div class="machine-node__vib-fill' + (esAlta ? " is-high" : "") + '" style="width:' + pct + '%"></div></div>' +
          '<span class="machine-node__vib-val">' + (vibracion !== null ? vibracion : "—") + '</span>' +
        '</div>' +
        (m.requiere_revision_preventiva ? '<span class="machine-node__flag">⚠ Revisar preventivo</span>' : '') +
      '</div>';

    hacerArrastrable(node);
    node.addEventListener("click", function (ev) {
      if (node.dataset.dragged === "1") { node.dataset.dragged = "0"; return; }
      abrirDrawer(m.codigo);
    });
    return node;
  }

  function dibujarConexiones(grupos) {
    var svgNS = "http://www.w3.org/2000/svg";
    while (linksSvg.firstChild) linksSvg.removeChild(linksSvg.firstChild);
    grupos.forEach(function (grupo) {
      for (var i = 0; i < grupo.maquinas.length - 1; i++) {
        var a = estado.posiciones[grupo.maquinas[i].codigo];
        var b = estado.posiciones[grupo.maquinas[i + 1].codigo];
        if (!a || !b) continue;
        var x1 = a.x + NODE_W, y1 = a.y + NODE_H / 2;
        var x2 = b.x, y2 = b.y + NODE_H / 2;
        var midX = (x1 + x2) / 2;
        var path = document.createElementNS(svgNS, "path");
        path.setAttribute("d", "M" + x1 + "," + y1 + " C " + midX + "," + y1 + " " + midX + "," + y2 + " " + x2 + "," + y2);
        path.setAttribute("class", "plant-link plant-link--anim");
        linksSvg.appendChild(path);
      }
    });
  }

  // ---------------------------------------------------------- drag & drop
  function hacerArrastrable(node) {
    var arrastrando = false, offX = 0, offY = 0;

    node.addEventListener("pointerdown", function (ev) {
      arrastrando = true;
      node.dataset.dragged = "0";
      node.classList.add("is-dragging");
      var rectCanvas = canvas.getBoundingClientRect();
      offX = ev.clientX - rectCanvas.left - node.offsetLeft;
      offY = ev.clientY - rectCanvas.top - node.offsetTop;
      node.setPointerCapture(ev.pointerId);
    });

    node.addEventListener("pointermove", function (ev) {
      if (!arrastrando) return;
      node.dataset.dragged = "1";
      var rectCanvas = canvas.getBoundingClientRect();
      var x = Math.max(0, ev.clientX - rectCanvas.left - offX);
      var y = Math.max(0, ev.clientY - rectCanvas.top - offY);
      node.style.left = x + "px";
      node.style.top = y + "px";
      estado.posiciones[node.dataset.codigo] = { x: x, y: y };
      dibujarConexiones(agruparPorLinea(estado.maquinas));
    });

    function soltar(ev) {
      if (!arrastrando) return;
      arrastrando = false;
      node.classList.remove("is-dragging");
      guardarLayout();
    }
    node.addEventListener("pointerup", soltar);
    node.addEventListener("pointercancel", soltar);
  }

  // ------------------------------------------------------------- feed
  function refrescar() {
    fetch(DATOS_URL).then(function (r) { return r.json(); }).then(function (data) {
      if (data.error) { refreshStatus.textContent = data.error; return; }
      render(data.maquinas || []);
      refreshStatus.textContent = "Actualizado " + new Date().toLocaleTimeString();
      if (estado.seleccionada) cargarDatosDrawer(estado.seleccionada, true);
    }).catch(function () { refreshStatus.textContent = "Sin conexión"; });
  }

  var datosIniciales = document.getElementById("maquinas-data");
  if (datosIniciales) {
    try { render(JSON.parse(datosIniciales.textContent) || []); } catch (e) {}
  }
  refrescar();
  setInterval(refrescar, 5000);

  // ------------------------------------------------------------- drawer
  var drawer = document.getElementById("machineDrawer");
  var drawerLinea = document.getElementById("drawerLinea");
  var drawerTitle = document.getElementById("drawerTitle");
  var drawerEstado = document.getElementById("drawerEstado");
  var drawerAlert = document.getElementById("drawerAlert");
  var drawerMtbf = document.getElementById("drawerMtbf");
  var drawerMttr = document.getElementById("drawerMttr");
  var drawerDispo = document.getElementById("drawerDispo");
  var drawerDispoFill = document.getElementById("drawerDispoFill");
  var drawerVibracion = document.getElementById("drawerVibracion");
  var drawerUmbral = document.getElementById("drawerUmbral");
  var drawerTemperatura = document.getElementById("drawerTemperatura");
  var drawerTimestamp = document.getElementById("drawerTimestamp");
  var trendChart = document.getElementById("trendChart");
  var trendEmpty = document.getElementById("trendEmpty");

  var drawerModoSelect = document.getElementById("drawerModoSelect");
  var drawerModoGuardar = document.getElementById("drawerModoGuardar");
  var drawerModoMsg = document.getElementById("drawerModoMsg");
  var drawerManualSection = document.getElementById("drawerManualSection");
  var drawerManualForm = document.getElementById("drawerManualForm");
  var drawerManualMsg = document.getElementById("drawerManualMsg");
  var drawerSimuladoSection = document.getElementById("drawerSimuladoSection");
  var drawerSimularBtn = document.getElementById("drawerSimularBtn");
  var drawerSimularMsg = document.getElementById("drawerSimularMsg");
  var drawerOpsForm = document.getElementById("drawerOpsForm");
  var drawerOpsMsg = document.getElementById("drawerOpsMsg");

  function abrirDrawer(codigo) {
    estado.seleccionada = codigo;
    drawer.setAttribute("aria-hidden", "false");
    var m = estado.maquinas.find(function (mm) { return mm.codigo === codigo; });
    pintarCabeceraDrawer(m);
    cargarDatosDrawer(codigo, false);
  }
  function cerrarDrawer() {
    drawer.setAttribute("aria-hidden", "true");
    estado.seleccionada = null;
  }
  document.getElementById("drawerClose").addEventListener("click", cerrarDrawer);
  document.getElementById("drawerBackdrop").addEventListener("click", cerrarDrawer);

  function pintarCabeceraDrawer(m) {
    if (!m) return;
    drawerLinea.textContent = m.linea || "Sin línea";
    drawerTitle.textContent = m.nombre + " · " + m.codigo;
    var estadoClase = estadoValido(m.estado_maquina);
    var etiquetas = { OPERA: "Operativa", MANTE: "En mantenimiento", FALLO: "En falla", sin: "Sin estado" };
    drawerEstado.textContent = etiquetas[estadoClase];
    drawerAlert.hidden = !m.requiere_revision_preventiva;
    drawerVibracion.textContent = m.ultima_lectura ? m.ultima_lectura.vibracion : "Sin datos";
    drawerUmbral.textContent = m.umbral_vibracion;
    drawerTemperatura.textContent = m.ultima_lectura && m.ultima_lectura.temperatura != null ? m.ultima_lectura.temperatura + " °C" : "—";
    drawerTimestamp.textContent = m.ultima_lectura ? m.ultima_lectura.timestamp.slice(0, 16).replace("T", " ") : "—";
    drawerModoSelect.value = m.modo_monitoreo || "simulado";
    actualizarSeccionesPorModo(m.modo_monitoreo);
    drawerModoMsg.hidden = true;
    drawerManualMsg.hidden = true;
    drawerSimularMsg.hidden = true;
    drawerOpsMsg.hidden = true;
  }

  function actualizarSeccionesPorModo(modo) {
    drawerManualSection.hidden = modo !== "manual";
    drawerSimuladoSection.hidden = modo !== "simulado";
  }

  // vista previa instantánea al elegir modo, sin esperar el clic en "Guardar"
  drawerModoSelect.addEventListener("change", function () {
    actualizarSeccionesPorModo(drawerModoSelect.value);
  });

  function mostrarMsg(el, texto, ok) {
    el.hidden = false;
    el.textContent = texto;
    el.className = "feedback-msg " + (ok ? "is-ok" : "is-error");
  }

  drawerModoGuardar.addEventListener("click", function () {
    if (!estado.seleccionada) return;
    var codigo = estado.seleccionada;
    fetch(urlPara(MODO_TPL, codigo), {
      method: "PATCH",
      headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
      body: JSON.stringify({ modo_monitoreo: drawerModoSelect.value }),
    }).then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
      .then(function (res) {
        if (!res.ok) {
          mostrarMsg(drawerModoMsg, typeof res.data === "object" ? JSON.stringify(res.data) : "No se pudo actualizar el modo.", false);
          return;
        }
        mostrarMsg(drawerModoMsg, "Modo actualizado a " + res.data.modo_monitoreo + ".", true);
        actualizarSeccionesPorModo(res.data.modo_monitoreo);
        refrescar();
      }).catch(function () { mostrarMsg(drawerModoMsg, "No fue posible conectar con el servidor.", false); });
  });

  drawerManualForm.addEventListener("submit", function (ev) {
    ev.preventDefault();
    if (!estado.seleccionada) return;
    var payload = {
      maquina: estado.seleccionada,
      vibracion: parseFloat(document.getElementById("mVibracion").value),
      temperatura: document.getElementById("mTemperatura").value ? parseFloat(document.getElementById("mTemperatura").value) : null,
      golpe: document.getElementById("mGolpe").checked,
    };
    fetch(LECTURA_MANUAL_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
      body: JSON.stringify(payload),
    }).then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
      .then(function (res) {
        if (!res.ok) {
          mostrarMsg(drawerManualMsg, typeof res.data === "object" ? JSON.stringify(res.data) : "No se pudo registrar la lectura.", false);
          return;
        }
        mostrarMsg(drawerManualMsg, res.data.reporte_automatico
          ? "Lectura registrada. Se generó un reporte de falla automático (#" + res.data.reporte_automatico + ")."
          : "Lectura registrada correctamente.", true);
        drawerManualForm.reset();
        refrescar();
        cargarDatosDrawer(estado.seleccionada, true);
      }).catch(function () { mostrarMsg(drawerManualMsg, "No fue posible conectar con el servidor.", false); });
  });

  drawerSimularBtn.addEventListener("click", function () {
    if (!estado.seleccionada) return;
    drawerSimularBtn.disabled = true;
    fetch(urlPara(SIMULAR_TPL, estado.seleccionada), {
      method: "POST",
      headers: { "X-CSRFToken": getCookie("csrftoken") },
    }).then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
      .then(function (res) {
        drawerSimularBtn.disabled = false;
        if (!res.ok) {
          mostrarMsg(drawerSimularMsg, typeof res.data === "object" ? JSON.stringify(res.data) : "No se pudo generar la lectura.", false);
          return;
        }
        mostrarMsg(drawerSimularMsg, res.data.reporte_automatico
          ? "Lectura simulada generada. Se creó un reporte de falla automático (#" + res.data.reporte_automatico + ")."
          : "Lectura simulada generada (vibración " + res.data.vibracion + ").", true);
        refrescar();
        cargarDatosDrawer(estado.seleccionada, true);
      }).catch(function () {
        drawerSimularBtn.disabled = false;
        mostrarMsg(drawerSimularMsg, "No fue posible conectar con el servidor.", false);
      });
  });

  drawerOpsForm.addEventListener("submit", function (ev) {
    ev.preventDefault();
    if (!estado.seleccionada) return;
    var payload = {
      fechaInicio: document.getElementById("opsFechaInicio").value,
      fechaFin: document.getElementById("opsFechaFin").value,
      horasOperacion: parseInt(document.getElementById("opsHoras").value, 10),
    };
    fetch(urlPara(REGISTRO_OPS_TPL, estado.seleccionada), {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
      body: JSON.stringify(payload),
    }).then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
      .then(function (res) {
        if (!res.ok) {
          mostrarMsg(drawerOpsMsg, typeof res.data === "object" ? JSON.stringify(res.data) : "No se pudo registrar el periodo.", false);
          return;
        }
        mostrarMsg(drawerOpsMsg, "Periodo registrado (" + res.data.horasOperacion + " h). MTBF recalculado.", true);
        drawerOpsForm.reset();
        cargarDatosDrawer(estado.seleccionada, true);
      }).catch(function () { mostrarMsg(drawerOpsMsg, "No fue posible conectar con el servidor.", false); });
  });

  function cargarDatosDrawer(codigo, silencioso) {
    Promise.all([
      fetch(urlPara(INDICADORES_TPL, codigo)).then(function (r) { return r.json(); }).catch(function () { return null; }),
      fetch(urlPara(HISTORIAL_TPL, codigo) + "?limite=20").then(function (r) { return r.json(); }).catch(function () { return null; }),
    ]).then(function (res) {
      pintarIndicadores(res[0]);
      pintarTendencia(res[1]);
    });
  }

  function pintarIndicadores(data) {
    if (!data) return;
    drawerMtbf.textContent = data.mtbf != null ? Number(data.mtbf).toFixed(1) : "—";
    drawerMttr.textContent = data.mttr != null ? Number(data.mttr).toFixed(1) : "—";
    var dispo = data.disponibilidad;
    drawerDispo.textContent = dispo != null ? dispo + " %" : "Sin datos aún";
    drawerDispoFill.style.width = (dispo != null ? dispo : 0) + "%";
  }

  function pintarTendencia(data) {
    while (trendChart.firstChild) trendChart.removeChild(trendChart.firstChild);
    if (!data || !data.lecturas || data.lecturas.length < 2) {
      trendEmpty.hidden = false;
      return;
    }
    trendEmpty.hidden = true;
    var svgNS = "http://www.w3.org/2000/svg";
    var lecturas = data.lecturas;
    var umbral = data.umbral_vibracion || 4;
    var valores = lecturas.map(function (l) { return l.vibracion; });
    var maxVal = Math.max(umbral * 1.15, Math.max.apply(null, valores));
    var w = 300, h = 90, pad = 6;
    function px(i) { return pad + (i / (lecturas.length - 1)) * (w - pad * 2); }
    function py(v) { return h - pad - (v / maxVal) * (h - pad * 2); }

    var umbralLinea = document.createElementNS(svgNS, "line");
    umbralLinea.setAttribute("x1", pad); umbralLinea.setAttribute("x2", w - pad);
    umbralLinea.setAttribute("y1", py(umbral)); umbralLinea.setAttribute("y2", py(umbral));
    umbralLinea.setAttribute("stroke", "#ef4444"); umbralLinea.setAttribute("stroke-dasharray", "4 4");
    umbralLinea.setAttribute("stroke-width", "1"); umbralLinea.setAttribute("opacity", "0.6");
    trendChart.appendChild(umbralLinea);

    var puntos = valores.map(function (v, i) { return px(i) + "," + py(v); }).join(" ");
    var polyline = document.createElementNS(svgNS, "polyline");
    polyline.setAttribute("points", puntos);
    polyline.setAttribute("fill", "none");
    polyline.setAttribute("stroke", "var(--color-primary)");
    polyline.setAttribute("stroke-width", "2");
    trendChart.appendChild(polyline);

    valores.forEach(function (v, i) {
      var c = document.createElementNS(svgNS, "circle");
      c.setAttribute("cx", px(i)); c.setAttribute("cy", py(v)); c.setAttribute("r", "2.5");
      c.setAttribute("fill", v > umbral ? "#ef4444" : "var(--color-primary)");
      trendChart.appendChild(c);
    });
  }

  // -------------------------------------------------- modal nueva máquina
  var modal = document.getElementById("newMachineModal");
  var form = document.getElementById("newMachineForm");
  var errorBox = document.getElementById("newMachineError");
  var catalogosCargados = false;

  document.getElementById("btnNuevaMaquina").addEventListener("click", function () {
    modal.setAttribute("aria-hidden", "false");
    if (!catalogosCargados) cargarCatalogos();
  });
  function cerrarModal() { modal.setAttribute("aria-hidden", "true"); errorBox.hidden = true; }
  document.getElementById("newMachineClose").addEventListener("click", cerrarModal);
  document.getElementById("newMachineCancel").addEventListener("click", cerrarModal);
  document.getElementById("newMachineBackdrop").addEventListener("click", cerrarModal);

  function llenarSelect(select, items, valueKey, labelKey, placeholder) {
    select.innerHTML = "";
    if (placeholder) {
      var opt0 = document.createElement("option");
      opt0.value = ""; opt0.textContent = placeholder;
      select.appendChild(opt0);
    }
    items.forEach(function (it) {
      var opt = document.createElement("option");
      opt.value = it[valueKey];
      opt.textContent = it[labelKey];
      if (it.marca !== undefined) opt.dataset.marca = it.marca;
      select.appendChild(opt);
    });
  }

  var todosLosModelos = [];
  function cargarCatalogos() {
    fetch(CATALOGOS_URL).then(function (r) { return r.json(); }).then(function (data) {
      catalogosCargados = true;
      llenarSelect(document.getElementById("fLinea"), data.lineas || [], "codigo", "nombre", "Sin línea");
      llenarSelect(document.getElementById("fTipo"), data.tipos_maquina || [], "numeroRegistro", "nombre", "Sin especificar");
      llenarSelect(document.getElementById("fMarca"), data.marcas || [], "clave", "nombre", "Sin especificar");
      llenarSelect(document.getElementById("fEstado"), data.estados_maquina || [], "codigo", "nombre");
      llenarSelect(document.getElementById("fModo"), data.modos_monitoreo || [], "valor", "etiqueta");
      todosLosModelos = data.modelos || [];
      filtrarModelos("");
    }).catch(function () {
      errorBox.hidden = false;
      errorBox.textContent = "No se pudieron cargar los catálogos.";
    });
  }
  function filtrarModelos(marca) {
    var lista = marca ? todosLosModelos.filter(function (m) { return m.marca === marca; }) : todosLosModelos;
    llenarSelect(document.getElementById("fModelo"), lista, "codigo", "nombre", "Sin especificar");
  }
  document.getElementById("fMarca").addEventListener("change", function (ev) { filtrarModelos(ev.target.value); });

  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    errorBox.hidden = true;
    var payload = {
      codigo: document.getElementById("fCodigo").value.trim(),
      nombre: document.getElementById("fNombre").value.trim(),
      descripcion: document.getElementById("fDescripcion").value.trim(),
      numeroSerie: document.getElementById("fSerie").value.trim(),
      linea: document.getElementById("fLinea").value || null,
      marca: document.getElementById("fMarca").value || null,
      modelo: document.getElementById("fModelo").value || null,
      tipo_maquina: document.getElementById("fTipo").value || null,
      estado_maquina: document.getElementById("fEstado").value || null,
      modo_monitoreo: document.getElementById("fModo").value,
      umbral_vibracion: parseFloat(document.getElementById("fUmbral").value) || 4.0,
    };
    fetch(CREAR_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
      body: JSON.stringify(payload),
    }).then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
      .then(function (res) {
        if (!res.ok) {
          errorBox.hidden = false;
          errorBox.textContent = typeof res.data === "object" ? JSON.stringify(res.data) : "No se pudo crear la máquina.";
          return;
        }
        cerrarModal();
        form.reset();
        refrescar();
      }).catch(function () {
        errorBox.hidden = false;
        errorBox.textContent = "No fue posible conectar con el servidor.";
      });
  });
})();
