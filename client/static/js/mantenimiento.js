(function () {
  "use strict";

  var root = document.querySelector(".ordenes");
  if (!root) return;

  // Error de la API (objeto DRF) -> JSON de varias líneas y bien indentado.
  // Si no es objeto, usa el texto recibido o un fallback genérico.
  function apiErrorLegible(data, fallback) {
    if (typeof data === "string" && data) return data;
    if (data && typeof data === "object") {
      var mensajes = [];
      if (Array.isArray(data.non_field_errors)) {
        data.non_field_errors.forEach(function (m) { mensajes.push(m); });
      }
      if (typeof data.detail === "string") {
        mensajes.push(data.detail);
      }
      Object.keys(data).forEach(function (k) {
        if (k === "non_field_errors" || k === "detail") return;
        var v = data[k];
        if (Array.isArray(v)) {
          v.forEach(function (m) { mensajes.push(k + ": " + m); });
        } else if (typeof v === "string") {
          mensajes.push(k + ": " + v);
        }
      });
      if (mensajes.length) return mensajes.join("\n");
    }
    return fallback || "Error en la solicitud.";
  }

  var DATOS_URL = root.dataset.datosUrl;
  var CREAR_URL = root.dataset.crearUrl;
  var ASIGNAR_TPL = root.dataset.asignarUrlBase;
  var INICIAR_TPL = root.dataset.iniciarUrlBase;
  var CERRAR_TPL = root.dataset.cerrarUrlBase;
  var ACTUALIZAR_TPL = root.dataset.actualizarUrlBase;
  var DETALLE_TPL = root.dataset.detalleUrlBase;
  var CANCELAR_TPL = root.dataset.cancelarUrlBase;
  var TAREAS_CREAR_URL = root.dataset.tareasCrearUrl;
  var TAREA_ORDEN_TPL = root.dataset.tareaOrdenUrlBase;
  var REPORTES_DISPONIBLES_URL = root.dataset.reportesDisponiblesUrl;
  var EXPORTAR_CSV_TPL = root.dataset.exportarCsvBase;
  var EXPORTAR_XLSX_TPL = root.dataset.exportarXlsxBase;
  var EXPORTAR_PDF_TPL = root.dataset.exportarPdfBase;
  var DOCUMENTO_TPL = root.dataset.documentoUrlBase;
  var ES_TECNICO = root.dataset.esTecnico === "1";
  var ES_ADMIN = root.dataset.esAdmin === "1";
  var NUMERO_NOMINA = root.dataset.numeroNomina;

  var trabajadoresEl = document.getElementById("trabajadores-data");
  var maquinasEl = document.getElementById("maquinas-data");
  var tareasEl = document.getElementById("tareas-data");
  var herramientasEl = document.getElementById("herramientas-data");
  var trabajadores = trabajadoresEl ? JSON.parse(trabajadoresEl.textContent || "[]") : [];
  var maquinas = maquinasEl ? JSON.parse(maquinasEl.textContent || "[]") : [];
  var tareas = tareasEl ? JSON.parse(tareasEl.textContent || "[]") : [];
  var herramientas = herramientasEl ? JSON.parse(herramientasEl.textContent || "[]") : [];

  var listEl = document.getElementById("ordenesList");
  var emptyEl = document.getElementById("ordenesEmpty");
  var filtroEstado = document.getElementById("filtroEstado");

  var estado = { ordenes: [], seleccionada: null };

  // -------------------------------------------------- multiselect de asignacion
  // Listbox nativo (<select multiple>) + buscador + contador para elegir
  // equipo/trabajadores, herramientas y tareas, tanto en el modal de "Nueva
  // orden" como en el editor del drawer. La seleccion se lee directo del
  // <select> (selectedOptions); no hace falta estado paralelo.
  function llenarMultiSelect(selectEl, items, valueKey, labelFn, disponibleFn) {
    if (!selectEl) return;
    selectEl.innerHTML = "";
    items.forEach(function (item) {
      var opt = document.createElement("option");
      opt.value = String(item[valueKey]);
      var etiqueta = labelFn(item);
      var disp = disponibleFn ? disponibleFn(item) : null;
      if (disp !== null) {
        etiqueta += " (" + disp + " disponibles)";
        if (disp <= 0) opt.disabled = true;
      }
      opt.textContent = etiqueta;
      selectEl.appendChild(opt);
    });
  }

  function leerMultiSelect(selectEl) {
    if (!selectEl) return [];
    return Array.prototype.slice.call(selectEl.selectedOptions).map(function (o) { return o.value; });
  }

  function seleccionarMultiSelect(selectEl, valores) {
    if (!selectEl) return;
    var set = {};
    (valores || []).forEach(function (v) { set[String(v)] = true; });
    Array.prototype.forEach.call(selectEl.options, function (o) {
      var seleccionado = !!set[o.value];
      o.selected = seleccionado;
      // Al editar, una herramienta ya asignada a esta orden puede haber
      // quedado deshabilitada por no tener disponibles; se rehabilita para
      // que la seleccion previa se conserve en pantalla.
      if (seleccionado && o.disabled) o.disabled = false;
    });
  }

  function contarMultiSelect(selectEl, contadorEl) {
    if (!selectEl || !contadorEl) return;
    var n = selectEl.selectedOptions.length;
    contadorEl.textContent = n + (n === 1 ? " seleccionado" : " seleccionados");
  }

  function filtrarMultiSelect(selectEl, inputEl) {
    if (!selectEl || !inputEl) return;
    var texto = (inputEl.value || "").trim().toLowerCase();
    Array.prototype.forEach.call(selectEl.options, function (o) {
      // Las ya seleccionadas siempre quedan visibles para no "perderlas"
      // de vista mientras se busca.
      if (o.selected) { o.hidden = false; return; }
      o.hidden = texto !== "" && o.textContent.toLowerCase().indexOf(texto) === -1;
    });
  }

  function pintarChipsEstaticos(listaEl, items, labelFn) {
    if (!listaEl) return;
    listaEl.innerHTML = "";
    if (!items || !items.length) {
      var vacio = document.createElement("span");
      vacio.className = "orden-asig__chip";
      vacio.textContent = "Ninguna";
      listaEl.appendChild(vacio);
      return;
    }
    items.forEach(function (item) {
      var chip = document.createElement("span");
      chip.className = "orden-asig__chip";
      chip.textContent = labelFn(item);
      listaEl.appendChild(chip);
    });
  }

  function etiquetaTrabajador(t) { return t.nombre + " " + (t.apellidoPat || "") + " (" + t.numeroNomina + ")"; }

  var _modalNuevaOrden = document.getElementById("newOrdenModal");
  var _drawerOrden = document.getElementById("ordenDrawer");
  var _modalReporteFalla = document.getElementById("reporteFallaPickerModal");
  var _drawerScrim = document.getElementById("ordenDrawerScrim");
  if (_modalNuevaOrden) conBloqueoScroll(_modalNuevaOrden);
  if (_modalReporteFalla) conBloqueoScroll(_modalReporteFalla);
  var _modalConfirmarCancelar = document.getElementById("confirmCancelarOrdenModal");
  if (_modalConfirmarCancelar) conBloqueoScroll(_modalConfirmarCancelar);

  // El drawer de orden ya NO usa .showModal(): un <dialog> abierto asi vive
  // en el "top layer" del navegador y se pinta encima de TODO sin importar
  // z-index, por eso antes había que cerrarlo para ver el modal de falla.
  // Manejandolo como panel normal (open + estilos) sí respeta el z-index.
  function abrirDrawerPanel() {
    document.body.style.overflow = "hidden";
    _drawerOrden.setAttribute("open", "");
    if (_drawerScrim) _drawerScrim.hidden = false;
  }
  function cerrarDrawerPanel() {
    document.body.style.overflow = "";
    _drawerOrden.removeAttribute("open");
    if (_drawerScrim) _drawerScrim.hidden = true;
  }
  if (_drawerScrim) _drawerScrim.addEventListener("click", cerrarDrawerPanel);

  // ------------------------------------------------- reporte de falla (crear orden)
  // Estado del reporte que el usuario eligio para adjuntar a la orden correctiva
  // en curso. Se resetea al cerrar/enviar el modal de "Nueva orden".
  var reporteSeleccionado = null;

  var oTipo = document.getElementById("oTipo");
  var oReporteFallaWrap = document.getElementById("oReporteFallaWrap");
  var oReporteFallaBtn = document.getElementById("oReporteFallaBtn");
  var oReporteFallaEmpty = document.getElementById("oReporteFallaEmpty");
  var oReporteFallaChip = document.getElementById("oReporteFallaChip");
  var oReporteFallaTexto = document.getElementById("oReporteFallaTexto");
  var oReporteFallaVer = document.getElementById("oReporteFallaVer");
  var oReporteFallaQuitar = document.getElementById("oReporteFallaQuitar");
  var rfLista = document.getElementById("rfLista");
  var rfEmpty = document.getElementById("rfEmpty");
  var rfCancelar = document.getElementById("rfCancelar");

  function limpiarReporteSeleccionado() {
    reporteSeleccionado = null;
    if (oReporteFallaEmpty) oReporteFallaEmpty.hidden = false;
    if (oReporteFallaChip) oReporteFallaChip.hidden = true;
  }

  function pintarReporteSeleccionado() {
    if (!reporteSeleccionado) { limpiarReporteSeleccionado(); return; }
    oReporteFallaEmpty.hidden = true;
    oReporteFallaChip.hidden = false;
    oReporteFallaTexto.textContent = "#" + reporteSeleccionado.numeroRegistro + " · " + reporteSeleccionado.asunto;
  }

  var oFechaWrap = document.getElementById("oFechaWrap");
  var oFecha = document.getElementById("oFecha");
  if (oTipo) {
    oTipo.addEventListener("change", function () {
      var esPreventivo = oTipo.value === "PREVE";
      if (oFechaWrap) oFechaWrap.hidden = !esPreventivo;
      if (oReporteFallaWrap) oReporteFallaWrap.hidden = oTipo.value !== "CORRE";
      if (oTipo.value !== "CORRE") limpiarReporteSeleccionado();
      if (oFecha) oFecha.required = esPreventivo;
    });
  }

  if (oReporteFallaBtn && _modalReporteFalla && rfLista) {
    oReporteFallaBtn.addEventListener("click", function () {
      var maquina = document.getElementById("oMaquina").value;
      if (!maquina) { errorNuevaOrden("Selecciona primero la máquina."); return; }
      rfLista.innerHTML = "<p>Cargando…</p>";
      rfEmpty.hidden = true;
      _modalReporteFalla.showModal();
      fetch(REPORTES_DISPONIBLES_URL + "?maquina=" + encodeURIComponent(maquina))
        .then(function (r) { return r.json(); })
        .then(function (data) {
          rfLista.innerHTML = "";
          var reportes = Array.isArray(data) ? data : [];
          rfEmpty.hidden = reportes.length > 0;
          reportes.forEach(function (rep) {
            var item = document.createElement("button");
            item.type = "button";
            item.className = "orden-reporte__item";
            item.innerHTML =
              '<span class="orden-reporte__item-asunto">#' + rep.numeroRegistro + " · " + rep.asunto + '</span>' +
              '<span class="orden-reporte__item-meta">' + (rep.tipo_severidad_nombre || "") + " · " + (rep.estado_reporte_nombre || "") + " · " + (rep.fechaCreacion || "") + '</span>';
            item.addEventListener("click", function () {
              reporteSeleccionado = { numeroRegistro: rep.numeroRegistro, asunto: rep.asunto };
              pintarReporteSeleccionado();
              _modalReporteFalla.close();
            });
            rfLista.appendChild(item);
          });
        })
        .catch(function () {
          rfLista.innerHTML = "";
          rfEmpty.hidden = false;
          rfEmpty.textContent = "No fue posible conectar con el servidor.";
        });
    });
  }

  if (rfCancelar && _modalReporteFalla) {
    rfCancelar.addEventListener("click", function () { _modalReporteFalla.close(); });
  }

  if (oReporteFallaVer) {
    oReporteFallaVer.addEventListener("click", function () {
      if (reporteSeleccionado && window.abrir_modal_detalle) {
        // Un <dialog> abierto con .showModal() vive en el "top layer" y se
        // pinta encima de todo sin importar z-index: si no lo cerramos, el
        // modal de la falla queda atrapado detras.
        if (_modalNuevaOrden && _modalNuevaOrden.open) _modalNuevaOrden.close();
        window.abrir_modal_detalle(reporteSeleccionado.numeroRegistro);
      }
    });
  }

  if (oReporteFallaQuitar) {
    oReporteFallaQuitar.addEventListener("click", function () { limpiarReporteSeleccionado(); });
  }

  // Si cambian de maquina despues de elegir un reporte, el reporte ya no
  // necesariamente corresponde: se limpia para evitar mandar un folio que
  // el backend va a rechazar por pertenecer a otra maquina.
  var _selectMaquinaGlobal = document.getElementById("oMaquina");
  if (_selectMaquinaGlobal) {
    _selectMaquinaGlobal.addEventListener("change", limpiarReporteSeleccionado);
  }

  function errorNuevaOrden(texto) {
    var errorEl = document.getElementById("newOrdenError");
    if (!errorEl) return;
    errorEl.hidden = false;
    errorEl.textContent = texto;
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
  function urlPara(tpl, folio) { return tpl.replace("__FOLIO__", encodeURIComponent(folio)); }

  function conBloqueoScroll(dialogEl) {
    dialogEl.addEventListener("close", function () { document.body.style.overflow = ""; });
    var _show = dialogEl.showModal.bind(dialogEl);
    dialogEl.showModal = function () { document.body.style.overflow = "hidden"; _show(); };
  }

  // ------------------------------------------------------------- fetch
  var _folioParaAbrir = new URLSearchParams(window.location.search).get("orden");
  var _autoEditar = new URLSearchParams(window.location.search).get("editar") === "1";

  function cargarOrdenes() {
    var params = new URLSearchParams();
    if (ES_TECNICO && NUMERO_NOMINA) params.set("trabajador", NUMERO_NOMINA);
    if (!ES_TECNICO && filtroEstado && filtroEstado.value) params.set("estado", filtroEstado.value);
    fetch(DATOS_URL + "?" + params.toString())
      .then(function (r) { return r.json(); })
      .then(function (data) {
        estado.ordenes = Array.isArray(data) ? data : [];
        pintarLista();
        if (_folioParaAbrir) {
          abrirDrawer(_folioParaAbrir);
          if (_autoEditar) {
            var editarBtnAuto = document.getElementById("ordenEditarBtn");
            if (editarBtnAuto) editarBtnAuto.click();
          }
          _folioParaAbrir = null;
          window.history.replaceState({}, "", window.location.pathname);
        }
      })
      .catch(function () {
        listEl.querySelectorAll(".orden-card").forEach(function (n) { n.remove(); });
        emptyEl.hidden = false;
        emptyEl.textContent = "No fue posible conectar con el servidor.";
      });
  }

  function pintarLista() {
    listEl.querySelectorAll(".orden-card").forEach(function (n) { n.remove(); });
    emptyEl.hidden = estado.ordenes.length > 0;
    emptyEl.textContent = "No hay órdenes para mostrar.";
    estado.ordenes.forEach(function (o) { listEl.appendChild(crearCard(o)); });
  }

  function crearCard(o) {
    var card = document.createElement("div");
    card.className = "orden-card";
    card.dataset.folio = o.folio;
    card.dataset.fechaprogramada = o.fechaprogramada || "";
    card.dataset.tipo = o.tipo_mantenimiento || "";
    card.dataset.maquina = o.maquina || "";
    card.innerHTML =
      '<div class="orden-card__top">' +
        '<span class="orden-card__folio">' + o.folio + '</span>' +
        '<span class="orden-card__estado orden-card__estado--' + o.estado_orden + '">' + (o.estado_orden_nombre || o.estado_orden || "—") + '</span>' +
      '</div>' +
      '<span class="orden-card__desc">' + o.descripcion + '</span>' +
      '<span class="orden-card__meta">' + (o.maquina_nombre || o.maquina || "Sin máquina") + " · " + (o.tipo_mantenimiento_nombre || o.tipo_mantenimiento || "") + '</span>' +
      '<span class="orden-card__meta">Asignada a: ' + (o.trabajador_nombre || "Sin asignar") + '</span>';
    card.addEventListener("click", function () {
      var cerrada = o.estado_orden === "CERRA" || o.estado_orden === "CANCE";
      if (cerrada && DOCUMENTO_TPL) {
        window.location.href = urlPara(DOCUMENTO_TPL, o.folio);
        return;
      }
      abrirDrawer(o.folio);
    });
    return card;
  }

  if (filtroEstado) filtroEstado.addEventListener("change", cargarOrdenes);

  // -------------------------------------------------------- crear orden
  var btnNueva = document.getElementById("btnNuevaOrden");
  var modal = document.getElementById("newOrdenModal");
  if (btnNueva && modal) {
    var form = document.getElementById("newOrdenForm");
    var errorEl = document.getElementById("newOrdenError");
    var selectMaquina = document.getElementById("oMaquina");
    var selectTrabajador = document.getElementById("oTrabajador");
    var oFecha = document.getElementById("oFecha");
    if (oFecha) oFecha.min = new Date().toISOString().slice(0, 10);

    maquinas.forEach(function (m) {
      var opt = document.createElement("option");
      opt.value = m.codigo; opt.textContent = m.codigo + " · " + m.nombre;
      selectMaquina.appendChild(opt);
    });
    trabajadores.forEach(function (t) {
      var opt = document.createElement("option");
      opt.value = t.numeroNomina; opt.textContent = t.nombre + " " + (t.apellidoPat || "") + " (" + t.numeroNomina + ")";
      selectTrabajador.appendChild(opt);
    });

    // ---- asignaciones: equipo / herramientas / tareas (multiselect + buscador) ----
    var oEquipoSelect = document.getElementById("oEquipoSelect");
    var oEquipoBuscar = document.getElementById("oEquipoBuscar");
    var oEquipoContador = document.getElementById("oEquipoContador");
    var oHerramientasSelect = document.getElementById("oHerramientasSelect");
    var oHerramientasBuscar = document.getElementById("oHerramientasBuscar");
    var oHerramientasContador = document.getElementById("oHerramientasContador");
    var oTareasSelect = document.getElementById("oTareasSelect");
    var oTareasBuscar = document.getElementById("oTareasBuscar");
    var oTareasContador = document.getElementById("oTareasContador");

    llenarMultiSelect(oEquipoSelect, trabajadores, "numeroNomina", etiquetaTrabajador);
    llenarMultiSelect(oHerramientasSelect, herramientas, "numeroregistro", function (h) { return h.nombre; }, function (h) { return (h.disponibles !== undefined) ? h.disponibles : null; });
    llenarMultiSelect(oTareasSelect, tareas, "numeroregistro", function (t) { return t.instruccion; });
    [
      [oEquipoSelect, oEquipoBuscar, oEquipoContador],
      [oHerramientasSelect, oHerramientasBuscar, oHerramientasContador],
      [oTareasSelect, oTareasBuscar, oTareasContador],
    ].forEach(function (tripla) {
      if (tripla[1]) tripla[1].addEventListener("input", function () { filtrarMultiSelect(tripla[0], tripla[1]); });
      if (tripla[0]) tripla[0].addEventListener("change", function () { contarMultiSelect(tripla[0], tripla[2]); });
    });

    // Admin: dar de alta una tarea nueva sobre la marcha (registro previo en TAREAS).
    var oNuevaTareaToggle = document.getElementById("oNuevaTareaToggle");
    var oNuevaTareaWrap = document.getElementById("oNuevaTareaWrap");
    var oNuevaTareaInput = document.getElementById("oNuevaTareaInput");
    var oNuevaTareaBtn = document.getElementById("oNuevaTareaBtn");
    if (oNuevaTareaToggle && oNuevaTareaWrap && TAREAS_CREAR_URL) {
      oNuevaTareaToggle.addEventListener("click", function () {
        oNuevaTareaWrap.hidden = false;
        oNuevaTareaToggle.hidden = true;
        if (oNuevaTareaInput) oNuevaTareaInput.focus();
      });
      function guardarNuevaTarea() {
        var texto = (oNuevaTareaInput && oNuevaTareaInput.value ? oNuevaTareaInput.value : "").trim();
        if (!texto) return;
        fetch(TAREAS_CREAR_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
          body: JSON.stringify({ instruccion: texto, actividad: true }),
        }).then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
          .then(function (res) {
            if (!res.ok) {
              errorEl.hidden = false;
              errorEl.textContent = apiErrorLegible(res.data, "No se pudo crear la tarea.");
              if (window.mostrarToast) mostrarToast(errorEl.textContent, "error");
              return;
            }
            tareas.push(res.data);
            if (res.data.numeroregistro == null) {
              errorEl.hidden = false;
              errorEl.textContent = "El API no devolvió el número de registro de la tarea.";
              if (window.mostrarToast) mostrarToast(errorEl.textContent, "error");
              return;
            }
            var opt = document.createElement("option");
            opt.value = String(res.data.numeroregistro);
            opt.textContent = res.data.instruccion;
            if (oTareasSelect) { oTareasSelect.appendChild(opt); opt.selected = true; contarMultiSelect(oTareasSelect, oTareasContador); }
            oNuevaTareaInput.value = "";
            oNuevaTareaWrap.hidden = true;
            oNuevaTareaToggle.hidden = false;
            if (window.mostrarToast) mostrarToast("Tarea creada.", "success");
          }).catch(function () {
            errorEl.hidden = false;
            errorEl.textContent = "No fue posible conectar con el servidor.";
            if (window.mostrarToast) mostrarToast(errorEl.textContent, "error");
          });
      }
      if (oNuevaTareaBtn) oNuevaTareaBtn.addEventListener("click", guardarNuevaTarea);
      if (oNuevaTareaInput) oNuevaTareaInput.addEventListener("keydown", function (e) {
        if (e.key === "Enter") { e.preventDefault(); guardarNuevaTarea(); }
      });
    }

    function abrirModal() { errorEl.hidden = true; errorEl.textContent = ""; modal.showModal(); }
    function cerrarModal() {
      modal.close();
      form.reset();
      limpiarReporteSeleccionado();
      if (oReporteFallaWrap) oReporteFallaWrap.hidden = true;
      if (oFechaWrap) oFechaWrap.hidden = false;
      if (oFecha) oFecha.required = true;
      [oEquipoSelect, oHerramientasSelect, oTareasSelect].forEach(function (sel) {
        if (!sel) return;
        Array.prototype.forEach.call(sel.options, function (o) { o.selected = false; o.hidden = false; });
      });
      [oEquipoBuscar, oHerramientasBuscar, oTareasBuscar].forEach(function (inp) { if (inp) inp.value = ""; });
      [oEquipoContador, oHerramientasContador, oTareasContador].forEach(function (c) { if (c) c.textContent = "0 seleccionados"; });
      if (oNuevaTareaWrap) oNuevaTareaWrap.hidden = true;
      if (oNuevaTareaToggle) oNuevaTareaToggle.hidden = false;
    }

    btnNueva.addEventListener("click", abrirModal);
    var btnCancelar = document.getElementById("newOrdenCancel");
    if (btnCancelar) btnCancelar.addEventListener("click", function (ev) { ev.preventDefault(); cerrarModal(); });

    (function abrirNuevaOrdenDesdeQuickAdd() {
      var params = new URLSearchParams(window.location.search);
      if (params.get("nueva_orden") === "1") {
        abrirModal();
        window.history.replaceState({}, "", window.location.pathname);
      }
    })();

    (function prellenarDesdeMonitoreo() {
      var params = new URLSearchParams(window.location.search);
      var maquinaParam = params.get("maquina");
      if (!maquinaParam) return;
      abrirModal();
      selectMaquina.value = maquinaParam;
      var tipoParam = params.get("tipo");
      var oTipoSelect = document.getElementById("oTipo");
      if (tipoParam && oTipoSelect) {
        oTipoSelect.value = tipoParam;
        oTipoSelect.dispatchEvent(new Event("change"));
      }
      var fechaParam = params.get("fecha");
      if (fechaParam && oFecha) oFecha.value = fechaParam;

      var reporteParam = params.get("reporte");
      if (reporteParam) {
        reporteSeleccionado = {
          numeroRegistro: reporteParam,
          asunto: params.get("asunto") || ("Reporte #" + reporteParam),
        };
        pintarReporteSeleccionado();
      }

      window.history.replaceState({}, "", window.location.pathname);
    })();

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var tipoMantenimiento = document.getElementById("oTipo").value;
      if (tipoMantenimiento === "CORRE" && !reporteSeleccionado) {
        errorNuevaOrden("Para órdenes correctivas es obligatorio adjuntar un reporte de falla.");
        if (window.mostrarToast) mostrarToast("Para órdenes correctivas es obligatorio adjuntar un reporte de falla.", "error");
        return;
      }
      var payload = {
        maquina: selectMaquina.value,
        tipo_mantenimiento: tipoMantenimiento,
        trabajador: selectTrabajador.value || null,
        fechaprogramada: document.getElementById("oFecha").value || null,
        descripcion: document.getElementById("oDescripcion").value,
        reporte_falla: reporteSeleccionado ? reporteSeleccionado.numeroRegistro : null,
        trabajadores: leerMultiSelect(oEquipoSelect),
        herramientas: leerMultiSelect(oHerramientasSelect),
        tareas: leerMultiSelect(oTareasSelect),
      };
      fetch(CREAR_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
        body: JSON.stringify(payload),
      }).then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
        .then(function (res) {
          if (!res.ok) {
            errorEl.hidden = false;
            errorEl.textContent = apiErrorLegible(res.data, "No se pudo crear la orden.");
            if (window.mostrarToast) mostrarToast(errorEl.textContent, "error");
            return;
          }
          cerrarModal();
          cargarOrdenes();
          if (window.mostrarToast) mostrarToast(res.data.folio ? "Orden " + res.data.folio + " creada." : "Orden creada.", "success");
        }).catch(function () {
          errorEl.hidden = false;
          errorEl.textContent = "No fue posible conectar con el servidor.";
          if (window.mostrarToast) mostrarToast(errorEl.textContent, "error");
        });
    });
  }

  // -------------------------------------------------------- drawer
  var drawer = document.getElementById("ordenDrawer");
  var msgEl = document.getElementById("ordenMsg");
  var asignarSelect = document.getElementById("ordenAsignarSelect");
  var btnAsignar = document.getElementById("ordenAsignarBtn");
  var btnIniciar = document.getElementById("ordenIniciarBtn");
  var btnVistaCompleta = document.getElementById("ordenVistaCompletaBtn");
  var formCerrar = document.getElementById("ordenCerrarForm");

  function mostrarMsg(texto, ok) {
    if (msgEl) {
      msgEl.textContent = texto;
      msgEl.className = ok ? "ok" : "error";
    }
    if (window.mostrarToast) mostrarToast(texto, ok ? "success" : "error");
  }
  function limpiarMsg() {
    if (!msgEl) return;
    msgEl.textContent = "";
    msgEl.className = "";
  }

  // ----------------------------------------- asociaciones (drawer)
  // El detalle viaja con un GET al endpoint de detalle; el listado solo trae
  // campos base, asi que los equipos/herramientas/tareas se piden aparte.
  var edEquipoSelect = document.getElementById("edEquipoSelect");
  var edEquipoBuscar = document.getElementById("edEquipoBuscar");
  var edEquipoContador = document.getElementById("edEquipoContador");
  var edHerramientasSelect = document.getElementById("edHerramientasSelect");
  var edHerramientasBuscar = document.getElementById("edHerramientasBuscar");
  var edHerramientasContador = document.getElementById("edHerramientasContador");
  var edTareasSelect = document.getElementById("edTareasSelect");
  var edTareasBuscar = document.getElementById("edTareasBuscar");
  var edTareasContador = document.getElementById("edTareasContador");
  [
    [edEquipoSelect, edEquipoBuscar, edEquipoContador],
    [edHerramientasSelect, edHerramientasBuscar, edHerramientasContador],
    [edTareasSelect, edTareasBuscar, edTareasContador],
  ].forEach(function (tripla) {
    if (tripla[1]) tripla[1].addEventListener("input", function () { filtrarMultiSelect(tripla[0], tripla[1]); });
    if (tripla[0]) tripla[0].addEventListener("change", function () { contarMultiSelect(tripla[0], tripla[2]); });
  });

  function cargarAsociaciones(folio) {
    if (!DETALLE_TPL) return Promise.resolve(null);
    return fetch(urlPara(DETALLE_TPL, folio))
      .then(function (r) { return r.json(); })
      .catch(function () { return null; });
  }

  function renderAsociacionesVista(det) {
    pintarChipsEstaticos(document.getElementById("ordenDrawerEquipo"), det ? (det.trabajadores || []) : [], etiquetaTrabajador);
    pintarChipsEstaticos(document.getElementById("ordenDrawerHerramientas"), det ? (det.herramientas || []) : [], function (h) { return h.nombre; });
    pintarChipsEstaticos(document.getElementById("ordenDrawerTareas"), det ? (det.tareas || []) : [], function (t) { return t.instruccion; });
    pintarChecklistTareas(det);
    pintarPorcentaje(det);
  }

  // Checklist de tareas para el tecnico: cada fila es un checkbox que
  // marca/desmarca el booleano verificacion en TAREA_ORDEN. Solo editable
  // mientras la orden esta ENPRO; en PROGR se ve pero bloqueado. El admin
  // conserva los chips estaticos (pintarChipsEstaticos de arriba).
  function pintarChecklistTareas(det) {
    var lista = document.getElementById("ordenChecklistTareas");
    if (!lista) return;
    lista.innerHTML = "";
    var tas = det ? (det.tareas || []) : [];
    if (!tas.length) {
      var vacio = document.createElement("span");
      vacio.className = "orden-asig__chip";
      vacio.textContent = "Ninguna";
      lista.appendChild(vacio);
      return;
    }
    var sel = estado.seleccionada;
    var habilitado = ES_TECNICO && sel && sel.estado_orden === "ENPRO";
    tas.forEach(function (t) {
      var fila = document.createElement("label");
      fila.className = "orden-checklist__item";
      var chk = document.createElement("input");
      chk.type = "checkbox";
      chk.checked = !!t.verificacion;
      chk.disabled = !habilitado;
      chk.addEventListener("change", function () {
        toggleTareaVerificacion(sel.folio, t.numeroregistro, chk.checked, chk);
      });
      fila.appendChild(chk);
      var txt = document.createElement("span");
      txt.textContent = t.instruccion;
      fila.appendChild(txt);
      lista.appendChild(fila);
    });
  }

  function pintarPorcentaje(det) {
    var porcEl = document.getElementById("ordenDrawerPorcentaje");
    if (!porcEl) return;
    var tas = det ? (det.tareas || []) : [];
    if (tas.length && det.porcentaje != null) {
      porcEl.hidden = false;
      porcEl.textContent = "· " + det.porcentaje + "%";
    } else {
      porcEl.hidden = true;
      porcEl.textContent = "";
    }
  }

  function toggleTareaVerificacion(folio, tarea, verificado, chk) {
    if (!TAREA_ORDEN_TPL) { chk.checked = !verificado; return; }
    fetch(TAREA_ORDEN_TPL
        .replace("__FOLIO__", encodeURIComponent(folio))
        .replace("__TAREA__", encodeURIComponent(tarea)), {
      method: "PATCH",
      headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
      body: JSON.stringify({ verificacion: verificado }),
    }).then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
      .then(function (res) {
        if (!res.ok) {
          chk.checked = !verificado;
          mostrarMsg("No se pudo actualizar la tarea.", false);
          return;
        }
        // El servidor recalcula el porcentaje de la orden: se refresca el
        // detalle para que el checklist y el progreso queden al dia.
        cargarAsociaciones(folio).then(function (det) {
          if (!estado.seleccionada || estado.seleccionada.folio !== folio) return;
          if (det) estado.seleccionada.detalle = det;
          renderAsociacionesVista(det || estado.seleccionada.detalle);
        });
      }).catch(function () {
        chk.checked = !verificado;
        mostrarMsg("Sin conexión.", false);
      });
  }

  function renderAsociacionesEdicion(det) {
    llenarMultiSelect(edEquipoSelect, trabajadores, "numeroNomina", etiquetaTrabajador);
    llenarMultiSelect(edHerramientasSelect, herramientas, "numeroregistro", function (h) { return h.nombre; }, function (h) { return (h.disponibles !== undefined) ? h.disponibles : null; });
    llenarMultiSelect(edTareasSelect, tareas, "numeroregistro", function (t) { return t.instruccion; });
    if (det) {
      seleccionarMultiSelect(edEquipoSelect, (det.trabajadores || []).map(function (t) { return t.numeroNomina; }));
      seleccionarMultiSelect(edHerramientasSelect, (det.herramientas || []).map(function (h) { return h.numeroregistro; }));
      seleccionarMultiSelect(edTareasSelect, (det.tareas || []).map(function (t) { return t.numeroregistro; }));
    }
    contarMultiSelect(edEquipoSelect, edEquipoContador);
    contarMultiSelect(edHerramientasSelect, edHerramientasContador);
    contarMultiSelect(edTareasSelect, edTareasContador);
  }

  function abrirDrawer(folio) {
    var orden = estado.ordenes.filter(function (o) { return o.folio === folio; })[0];
    if (!orden) return;
    estado.seleccionada = orden;
    limpiarMsg();

    var editarBtn = document.getElementById("ordenEditarBtn");
    var editDiv = document.getElementById("ordenDrawerEdit");

    // Reset edit mode
    if (editDiv) editDiv.hidden = true;
    if (editarBtn) editarBtn.hidden = false;

    document.getElementById("ordenDrawerFolio").textContent = orden.folio;
    document.getElementById("ordenDrawerTitle").textContent = orden.tipo_mantenimiento_nombre || orden.tipo_mantenimiento;
    document.getElementById("ordenDrawerInfo").textContent =
      (orden.maquina_nombre || orden.maquina || "Sin máquina") + " · " +
      (orden.estado_orden_nombre || orden.estado_orden) + " · Asignada a: " +
      (orden.trabajador_nombre || "Sin asignar");
    document.getElementById("ordenDrawerDescripcion").textContent = orden.descripcion || "";

    // Pre-fill edit inputs
    var edDesc = document.getElementById("edDescripcion");
    var edFecha = document.getElementById("edFecha");
    var edNotas = document.getElementById("edNotas");
    var edDiag = document.getElementById("edDiagnostico");
    var edHoras = document.getElementById("edHoras");
    var edFechaWrap = document.getElementById("edFechaWrap");
    if (edDesc) edDesc.value = orden.descripcion || "";
    if (edFecha) edFecha.value = orden.fechaprogramada || "";
    if (edNotas) edNotas.value = orden.notas || "";
    if (edDiag) edDiag.value = orden.diagnostico || "";
    if (edHoras) edHoras.value = orden.horasintervenidas != null ? orden.horasintervenidas : "";
    if (edFechaWrap) edFechaWrap.hidden = (orden.tipo_mantenimiento || "") !== "PREVE";

    var reporteWrap = document.getElementById("ordenDrawerReporte");
    if (reporteWrap) {
      reporteWrap.hidden = !orden.reporte_falla;
      var btnVerReporte = document.getElementById("ordenDrawerVerReporte");
      if (orden.reporte_falla && btnVerReporte) {
        btnVerReporte.textContent = "📄 Ver reporte de falla: #" + orden.reporte_falla + (orden.reporte_falla_asunto ? " · " + orden.reporte_falla_asunto : "");
      }
    }

    // La tarjeta de la lista usa estado_orden para decidir el color/etiqueta
    // "Cerrada"; el drawer debe usar la misma fuente de verdad en vez de
    // confiar solo en fechacierre, que puede venir vacío en ordenes viejas
    // o cerradas fuera del flujo normal.
    var cerrada = orden.estado_orden === "CERRA" || orden.estado_orden === "CANCE" || !!orden.fechacierre;

    if (asignarSelect && btnAsignar) {
      var seccionAsignar = asignarSelect.closest("label") || asignarSelect;
      seccionAsignar.hidden = cerrada;
      btnAsignar.hidden = cerrada;
      asignarSelect.innerHTML = "";
      trabajadores.forEach(function (t) {
        var opt = document.createElement("option");
        opt.value = t.numeroNomina; opt.textContent = t.nombre + " " + (t.apellidoPat || "") + " (" + t.numeroNomina + ")";
        asignarSelect.appendChild(opt);
      });
      // Arranca en quien ya tiene la orden (si aplica), para que solo cambie
      // de dueño si el admin de verdad elige a otra persona a proposito.
      if (orden.trabajador) asignarSelect.value = orden.trabajador;
      // Si la orden ya tiene alguien asignado, esto ya no es "asignar" sino
      // "reasignar": se le quita a quien la tenia y pasa a la persona nueva.
      var yaAsignada = !!orden.trabajador_nombre;
      var labelAsignar = document.getElementById("ordenAsignarLabel");
      var btnAsignarTexto = document.getElementById("ordenAsignarBtnTexto");
      if (labelAsignar) labelAsignar.textContent = yaAsignada ? "Reasignar" : "Asignar";
      if (btnAsignarTexto) btnAsignarTexto.textContent = yaAsignada ? "Reasignar" : "Asignar";
    }

    if (btnIniciar) btnIniciar.hidden = !ES_TECNICO || cerrada || (orden.estado_orden !== "PROGR" && orden.estado_orden !== "SOLIC");

    // El formulario de cierre (diagnostico/notas/horas/piezas) solo debe
    // verse cuando la orden YA esta en progreso: mientras esta "PROGR" el
    // tecnico solo debe ver info + "Marcar en progreso".
    var puedeLlenar = ES_TECNICO && !cerrada && orden.estado_orden === "ENPRO";
    if (formCerrar) formCerrar.hidden = !puedeLlenar;

    // "Vista completa" debe ofrecerse en cuanto el tecnico tiene algo que
    // hacer con su propia orden abierta (programada o ya en progreso), no
    // solo cuando ya esta en progreso: es la salida hacia el formulario
    // completo y validado de documento_orden.html.
    var puedeVerCompleta = ES_TECNICO && !cerrada && (orden.estado_orden === "PROGR" || orden.estado_orden === "SOLIC" || orden.estado_orden === "ENPRO");
    if (btnVistaCompleta) btnVistaCompleta.hidden = !puedeVerCompleta;

    // El tecnico solo puede exportar una orden ya cerrada (mientras sigue
    // abierta no hay diagnostico/notas/horas/piezas que documentar todavia).
    // El admin conserva el boton siempre visible, igual que en la vista
    // completa (documento_orden.html).
    if (exportBtn) exportBtn.hidden = ES_TECNICO && !cerrada;

    // Cancelacion (solo admin y mientras la orden no este cerrada/cancelada).
    var cancelarBtn = document.getElementById("ordenCancelarBtn");
    if (cancelarBtn) cancelarBtn.hidden = !ES_ADMIN || cerrada;

    abrirDrawerPanel();

    // Asociaciones: se piden al detalle y se pintan tanto en modo vista como
    // en el editor. De paso completan los campos que el listado no trae.
    renderAsociacionesVista(null);
    renderAsociacionesEdicion(null);
    cargarAsociaciones(folio).then(function (det) {
      if (!estado.seleccionada || estado.seleccionada.folio !== folio) return;
      estado.seleccionada.detalle = det || estado.seleccionada.detalle;
      renderAsociacionesVista(det);
      renderAsociacionesEdicion(det);
      if (!det) return;
      if (edDesc) edDesc.value = det.descripcion || "";
      if (edFecha) edFecha.value = det.fechaprogramada || "";
      if (edNotas) edNotas.value = det.notas || "";
      if (edDiag) edDiag.value = det.diagnostico || "";
      if (edHoras) edHoras.value = det.horasintervenidas != null ? det.horasintervenidas : "";
      if (edFechaWrap) edFechaWrap.hidden = (det.tipo_mantenimiento || "") !== "PREVE";
    });
  }

  var btnCerrarDrawer = document.getElementById("ordenDrawerClose");
  if (btnCerrarDrawer) btnCerrarDrawer.addEventListener("click", function () { cerrarDrawerPanel(); estado.seleccionada = null; });

  // El drawer ya no se cierra para mostrar el reporte de falla: al ser un
  // panel normal (no showModal), respeta el z-index frente al modal.
  var btnVerReporteDrawer = document.getElementById("ordenDrawerVerReporte");
  if (btnVerReporteDrawer) {
    btnVerReporteDrawer.addEventListener("click", function () {
      if (estado.seleccionada && estado.seleccionada.reporte_falla && window.abrir_modal_detalle) {
        document.getElementById("detalle-falla").classList.add("fallas-modal--junto-drawer");
        window.abrir_modal_detalle(estado.seleccionada.reporte_falla);
      }
    });
  }

  document.addEventListener("fallas:modal-cerrado", function () {
    document.getElementById("detalle-falla").classList.remove("fallas-modal--junto-drawer");
  });

  if (btnAsignar && asignarSelect) {
    btnAsignar.addEventListener("click", function () {
      if (!estado.seleccionada) return;
      var trabajador = asignarSelect.value;
      if (!trabajador) return;
      fetch(urlPara(ASIGNAR_TPL, estado.seleccionada.folio), {
        method: "PATCH",
        headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
        body: JSON.stringify({ trabajador: trabajador }),
      }).then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
        .then(function (res) {
          if (!res.ok) { mostrarMsg("No se pudo asignar.", false); return; }
          mostrarMsg("Trabajador asignado.", true);
          cerrarDrawerPanel();
          cargarOrdenes();
        }).catch(function () { mostrarMsg("Sin conexión.", false); });
    });
  }

  if (btnIniciar) {
    btnIniciar.addEventListener("click", function () {
      if (!estado.seleccionada) return;
      var folio = estado.seleccionada.folio;
      fetch(urlPara(INICIAR_TPL, folio), {
        method: "PATCH",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
      }).then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
        .then(function (res) {
          if (!res.ok) { mostrarMsg("No se pudo actualizar.", false); return; }
          if (ES_TECNICO && DOCUMENTO_TPL) {
            // El tecnico pasa directo a la vista formal (la misma de una
            // orden cerrada) para llenar diagnostico/notas/horas/piezas.
            window.location.href = urlPara(DOCUMENTO_TPL, folio);
            return;
          }
          mostrarMsg("Orden marcada en progreso.", true);
          cerrarDrawerPanel();
          cargarOrdenes();
        }).catch(function () { mostrarMsg("Sin conexión.", false); });
    });
  }

  if (btnVistaCompleta) {
    btnVistaCompleta.addEventListener("click", function () {
      if (!estado.seleccionada || !DOCUMENTO_TPL) return;
      window.location.href = urlPara(DOCUMENTO_TPL, estado.seleccionada.folio);
    });
  }

  // ----------------------------------------------- editar orden
  var editarBtn = document.getElementById("ordenEditarBtn");
  var editDiv = document.getElementById("ordenDrawerEdit");
  var guardarBtn = document.getElementById("ordenGuardarBtn");
  var cancelarEditBtn = document.getElementById("ordenCancelarEditBtn");

  if (editarBtn && editDiv) {
    editarBtn.addEventListener("click", function () {
      editDiv.hidden = false;
      editarBtn.hidden = true;
    });
  }

  if (guardarBtn && editDiv) {
    guardarBtn.addEventListener("click", function () {
      if (!estado.seleccionada) return;
      var editForm = document.getElementById("ordenEditForm");
      if (editForm && !editForm.checkValidity()) return;
      var payload = {
        descripcion: document.getElementById("edDescripcion").value,
        fechaprogramada: document.getElementById("edFecha").value || null,
        notas: document.getElementById("edNotas").value,
        diagnostico: document.getElementById("edDiagnostico").value,
        horasintervenidas: document.getElementById("edHoras").value,
        trabajadores: leerMultiSelect(edEquipoSelect),
        herramientas: leerMultiSelect(edHerramientasSelect),
        tareas: leerMultiSelect(edTareasSelect),
      };
      fetch(urlPara(ACTUALIZAR_TPL, estado.seleccionada.folio), {
        method: "PATCH",
        headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
        body: JSON.stringify(payload),
      }).then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
        .then(function (res) {
          if (!res.ok) { mostrarMsg(apiErrorLegible(res.data, "No se pudo actualizar."), false); return; }
          mostrarMsg("Orden actualizada.", true);
          cerrarDrawerPanel();
          cargarOrdenes();
        }).catch(function () { mostrarMsg("Sin conexión.", false); });
    });
  }

  if (cancelarEditBtn && editDiv && editarBtn) {
    cancelarEditBtn.addEventListener("click", function () {
      editDiv.hidden = true;
      editarBtn.hidden = false;
    });
  }

  // -------------------------------------------------- cancelar orden
  var ordenCancelarBtn = document.getElementById("ordenCancelarBtn");
  var confirmarCancelarBtn = document.getElementById("btnConfirmarCancelarSi");
  var rechazarCancelarBtn = document.getElementById("btnConfirmarCancelarNo");

  if (ordenCancelarBtn && _modalConfirmarCancelar) {
    ordenCancelarBtn.addEventListener("click", function () {
      if (!estado.seleccionada) return;
      var txt = document.getElementById("confirmCancelarOrdenTexto");
      if (txt) txt.textContent = "¿Cancelar la orden " + estado.seleccionada.folio + "? Quedará marcada como cancelada y su reporte de falla volverá a estar disponible.";
      _modalConfirmarCancelar.showModal();
    });
  }
  if (rechazarCancelarBtn && _modalConfirmarCancelar) {
    rechazarCancelarBtn.addEventListener("click", function () { _modalConfirmarCancelar.close(); });
  }
  if (confirmarCancelarBtn && _modalConfirmarCancelar) {
    confirmarCancelarBtn.addEventListener("click", function () {
      if (!estado.seleccionada) return;
      var folio = estado.seleccionada.folio;
      confirmarCancelarBtn.disabled = true;
      fetch(urlPara(CANCELAR_TPL, folio), {
        method: "PATCH",
        headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
      }).then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
        .then(function (res) {
          confirmarCancelarBtn.disabled = false;
          _modalConfirmarCancelar.close();
          if (!res.ok) { mostrarMsg("No se pudo cancelar la orden.", false); return; }
          mostrarMsg("Orden cancelada.", true);
          cerrarDrawerPanel();
          cargarOrdenes();
        }).catch(function () {
          confirmarCancelarBtn.disabled = false;
          _modalConfirmarCancelar.close();
          mostrarMsg("Sin conexión.", false);
        });
    });
  }

  if (formCerrar) {
    formCerrar.addEventListener("submit", function (ev) {
      ev.preventDefault();
      if (!estado.seleccionada) return;
      var folio = estado.seleccionada.folio;
      var payload = {
        diagnostico: document.getElementById("cDiagnostico").value,
        notas: document.getElementById("cNotas").value,
        horasIntervenidas: parseFloat(document.getElementById("cHoras").value),
      };
      fetch(urlPara(CERRAR_TPL, folio), {
        method: "PATCH",
        headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
        body: JSON.stringify(payload),
      }).then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
        .then(function (res) {
          if (!res.ok) {
            mostrarMsg(apiErrorLegible(res.data, "No se pudo cerrar la orden."), false);
            return;
          }
          mostrarMsg("Orden cerrada. Indicadores actualizados.", true);
          cerrarDrawerPanel();
          cargarOrdenes();
        }).catch(function () { mostrarMsg("Sin conexión.", false); });
    });
  }

  // -------------------------------------------------- exportar orden (modal)
  var exportBtn = document.getElementById("ordenExportarBtn");
  var exportModal = document.getElementById("exportar-orden");

  if (exportBtn && exportModal) {
    exportBtn.addEventListener("click", function () {
      if (!estado.seleccionada) return;
      var folio = estado.seleccionada.folio;
      document.getElementById("export-orden-folio").textContent = folio;
      document.getElementById("export-orden-csv-link").href  = urlPara(EXPORTAR_CSV_TPL, folio);
      document.getElementById("export-orden-xlsx-link").href = urlPara(EXPORTAR_XLSX_TPL, folio);
      document.getElementById("export-orden-pdf-link").href  = urlPara(EXPORTAR_PDF_TPL, folio);
      exportModal.classList.add("is-open");
    });

    // Si la orden tiene reporte de falla asociado, preguntamos si debe
    // incluirse en el mismo archivo antes de iniciar la descarga.
    var confirmFallaModal = document.getElementById("confirmFallaPdfModal");
    var pdfLink = document.getElementById("export-orden-pdf-link");
    if (confirmFallaModal && pdfLink) {
      pdfLink.addEventListener("click", function (ev) {
        var ordenSel = estado.seleccionada;
        if (!ordenSel || !ordenSel.reporte_falla) return;
        ev.preventDefault();
        var pdfUrl = urlPara(EXPORTAR_PDF_TPL, ordenSel.folio);
        document.getElementById("confirmFallaPdfTexto").textContent =
          "Esta orden tiene el reporte de falla \"" +
          (ordenSel.reporte_falla_asunto || ("#" + ordenSel.reporte_falla)) +
          "\" asociado. ¿Quieres incluirlo en el mismo PDF?";
        confirmFallaModal.showModal();

        document.getElementById("btnConfirmFallaSi").onclick = function () {
          window.location.href = pdfUrl + "?incluir_falla=1";
          confirmFallaModal.close();
          exportModal.classList.remove("is-open");
        };
        document.getElementById("btnConfirmFallaSolo").onclick = function () {
          window.location.href = pdfUrl;
          confirmFallaModal.close();
          exportModal.classList.remove("is-open");
        };
        document.getElementById("btnConfirmFallaCancelar").onclick = function () {
          confirmFallaModal.close();
        };
      });
    }

    $(document).on("click", "[data-dismiss='modal-export-orden']", function () {
      exportModal.classList.remove("is-open");
    });
    $(document).on("keydown", function (e) {
      if (e.key === "Escape") exportModal.classList.remove("is-open");
    });
  }

  // Exponer drawer para la pagina de calendario
  window.__estado = estado;
  window.__abrirDrawer = abrirDrawer;
  window.__cerrarDrawerPanel = cerrarDrawerPanel;
  window.__cargarOrdenes = cargarOrdenes;

  cargarOrdenes();
})();