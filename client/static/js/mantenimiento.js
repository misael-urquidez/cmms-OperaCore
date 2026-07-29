(function () {
  "use strict";

  var root = document.querySelector(".ordenes");
  if (!root) return;

  var DATOS_URL = root.dataset.datosUrl;
  var CREAR_URL = root.dataset.crearUrl;
  var ASIGNAR_TPL = root.dataset.asignarUrlBase;
  var INICIAR_TPL = root.dataset.iniciarUrlBase;
  var CERRAR_TPL = root.dataset.cerrarUrlBase;
  var REPORTES_DISPONIBLES_URL = root.dataset.reportesDisponiblesUrl;
  var ES_TECNICO = root.dataset.esTecnico === "1";
  var NUMERO_NOMINA = root.dataset.numeroNomina;

  var trabajadoresEl = document.getElementById("trabajadores-data");
  var maquinasEl = document.getElementById("maquinas-data");
  var piezasEl = document.getElementById("piezas-data");
  var refaccionesEl = document.getElementById("refacciones-data");
  var trabajadores = trabajadoresEl ? JSON.parse(trabajadoresEl.textContent || "[]") : [];
  var maquinas = maquinasEl ? JSON.parse(maquinasEl.textContent || "[]") : [];
  var piezas = piezasEl ? JSON.parse(piezasEl.textContent || "[]") : [];
  var refacciones = refaccionesEl ? JSON.parse(refaccionesEl.textContent || "[]") : [];

  var listEl = document.getElementById("ordenesList");
  var emptyEl = document.getElementById("ordenesEmpty");
  var filtroEstado = document.getElementById("filtroEstado");

  var estado = { ordenes: [], seleccionada: null };

  var _modalNuevaOrden = document.getElementById("newOrdenModal");
  var _drawerOrden = document.getElementById("ordenDrawer");
  var _modalReporteFalla = document.getElementById("reporteFallaPickerModal");
  var _drawerScrim = document.getElementById("ordenDrawerScrim");
  if (_modalNuevaOrden) conBloqueoScroll(_modalNuevaOrden);
  if (_modalReporteFalla) conBloqueoScroll(_modalReporteFalla);

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

  if (oTipo && oReporteFallaWrap) {
    oTipo.addEventListener("change", function () {
      oReporteFallaWrap.hidden = oTipo.value !== "CORRE";
      if (oTipo.value !== "CORRE") limpiarReporteSeleccionado();
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
  function cargarOrdenes() {
    var params = new URLSearchParams();
    if (ES_TECNICO && NUMERO_NOMINA) params.set("trabajador", NUMERO_NOMINA);
    if (!ES_TECNICO && filtroEstado && filtroEstado.value) params.set("estado", filtroEstado.value);
    fetch(DATOS_URL + "?" + params.toString())
      .then(function (r) { return r.json(); })
      .then(function (data) {
        estado.ordenes = Array.isArray(data) ? data : [];
        pintarLista();
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
    card.innerHTML =
      '<div class="orden-card__top">' +
        '<span class="orden-card__folio">' + o.folio + '</span>' +
        '<span class="orden-card__estado orden-card__estado--' + o.estado_orden + '">' + (o.estado_orden_nombre || o.estado_orden || "—") + '</span>' +
      '</div>' +
      '<span class="orden-card__desc">' + o.descripcion + '</span>' +
      '<span class="orden-card__meta">' + (o.maquina_nombre || o.maquina || "Sin máquina") + " · " + (o.tipo_mantenimiento_nombre || o.tipo_mantenimiento || "") + '</span>' +
      '<span class="orden-card__meta">Asignada a: ' + (o.trabajador_nombre || "Sin asignar") + '</span>';
    card.addEventListener("click", function () { abrirDrawer(o.folio); });
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

    maquinas.forEach(function (m) {
      var opt = document.createElement("option");
      opt.value = m.codigo; opt.textContent = m.codigo + " · " + m.nombre;
      selectMaquina.appendChild(opt);
    });
    trabajadores.forEach(function (t) {
      var opt = document.createElement("option");
      opt.value = t.numeroNomina; opt.textContent = t.nombre + " " + (t.apellidoPat || "");
      selectTrabajador.appendChild(opt);
    });

    function abrirModal() { errorEl.hidden = true; errorEl.textContent = ""; modal.showModal(); }
    function cerrarModal() {
      modal.close();
      form.reset();
      limpiarReporteSeleccionado();
      if (oReporteFallaWrap) oReporteFallaWrap.hidden = true;
    }

    btnNueva.addEventListener("click", abrirModal);
    var btnCancelar = document.getElementById("newOrdenCancel");
    if (btnCancelar) btnCancelar.addEventListener("click", function (ev) { ev.preventDefault(); cerrarModal(); });

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var payload = {
        maquina: selectMaquina.value,
        tipo_mantenimiento: document.getElementById("oTipo").value,
        trabajador: selectTrabajador.value || null,
        fechaprogramada: document.getElementById("oFecha").value || null,
        descripcion: document.getElementById("oDescripcion").value,
        reporte_falla: reporteSeleccionado ? reporteSeleccionado.numeroRegistro : null,
      };
      fetch(CREAR_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
        body: JSON.stringify(payload),
      }).then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
        .then(function (res) {
          if (!res.ok) {
            errorEl.hidden = false;
            errorEl.textContent = typeof res.data === "object" ? JSON.stringify(res.data) : "No se pudo crear la orden.";
            return;
          }
          cerrarModal();
          cargarOrdenes();
        }).catch(function () {
          errorEl.hidden = false;
          errorEl.textContent = "No fue posible conectar con el servidor.";
        });
    });
  }

  // -------------------------------------------------------- drawer
  var drawer = document.getElementById("ordenDrawer");
  var msgEl = document.getElementById("ordenMsg");
  var asignarSelect = document.getElementById("ordenAsignarSelect");
  var btnAsignar = document.getElementById("ordenAsignarBtn");
  var btnIniciar = document.getElementById("ordenIniciarBtn");
  var formCerrar = document.getElementById("ordenCerrarForm");

  function mostrarMsg(texto, ok) {
    if (!msgEl) return;
    msgEl.textContent = texto;
    msgEl.className = ok ? "ok" : "error";
  }
  function limpiarMsg() {
    if (!msgEl) return;
    msgEl.textContent = "";
    msgEl.className = "";
  }

  function abrirDrawer(folio) {
    var orden = estado.ordenes.filter(function (o) { return o.folio === folio; })[0];
    if (!orden) return;
    estado.seleccionada = orden;
    limpiarMsg();

    document.getElementById("ordenDrawerFolio").textContent = orden.folio;
    document.getElementById("ordenDrawerTitle").textContent = orden.tipo_mantenimiento_nombre || orden.tipo_mantenimiento;
    document.getElementById("ordenDrawerInfo").textContent =
      (orden.maquina_nombre || orden.maquina || "Sin máquina") + " · " +
      (orden.estado_orden_nombre || orden.estado_orden) + " · Asignada a: " +
      (orden.trabajador_nombre || "Sin asignar");
    document.getElementById("ordenDrawerDescripcion").textContent = orden.descripcion || "";

    var reporteWrap = document.getElementById("ordenDrawerReporte");
    if (reporteWrap) {
      reporteWrap.hidden = !orden.reporte_falla;
      var btnVerReporte = document.getElementById("ordenDrawerVerReporte");
      if (orden.reporte_falla && btnVerReporte) {
        btnVerReporte.textContent = "📄 Ver reporte de falla: #" + orden.reporte_falla + (orden.reporte_falla_asunto ? " · " + orden.reporte_falla_asunto : "");
      }
    }

    var cerrada = !!orden.fechacierre;

    if (asignarSelect && btnAsignar) {
      var seccionAsignar = asignarSelect.closest("label") || asignarSelect;
      seccionAsignar.hidden = cerrada;
      btnAsignar.hidden = cerrada;
      asignarSelect.innerHTML = "";
      trabajadores.forEach(function (t) {
        var opt = document.createElement("option");
        opt.value = t.numeroNomina; opt.textContent = t.nombre + " " + (t.apellidoPat || "");
        asignarSelect.appendChild(opt);
      });
    }

    if (btnIniciar) btnIniciar.hidden = cerrada || orden.estado_orden !== "PROGR";
    if (formCerrar) formCerrar.hidden = cerrada || !(ES_TECNICO && (orden.estado_orden === "ENPRO" || orden.estado_orden === "PROGR"));

    // Piezas disponibles para "reemplaza" = solo las de esta maquina.
    refrescarSelectPiezas(orden.maquina);
    movPendientes = [];
    pintarMovPendientes();

    abrirDrawerPanel();
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
      fetch(urlPara(INICIAR_TPL, estado.seleccionada.folio), {
        method: "PATCH",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
      }).then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
        .then(function (res) {
          if (!res.ok) { mostrarMsg("No se pudo actualizar.", false); return; }
          mostrarMsg("Orden marcada en progreso.", true);
          cerrarDrawerPanel();
          cargarOrdenes();
        }).catch(function () { mostrarMsg("Sin conexión.", false); });
    });
  }

  // -------------------------------------------------- movimientos (cierre)
  var movPendientes = []; // [{refaccion, refaccionNombre, pieza, piezaNombre}]
  var movList = document.getElementById("ordenMovList");
  var movAddBtn = document.getElementById("ordenMovAddBtn");
  var movForm = document.getElementById("ordenMovForm");
  var movRefaccion = document.getElementById("ordenMovRefaccion");
  var movPieza = document.getElementById("ordenMovPieza");
  var movConfirmar = document.getElementById("ordenMovConfirmar");
  var movCancelar = document.getElementById("ordenMovCancelar");

  function llenarSelect(select, items, valueKey, labelFn) {
    select.querySelectorAll("option:not(:first-child)").forEach(function (o) { o.remove(); });
    items.forEach(function (it) {
      var opt = document.createElement("option");
      opt.value = it[valueKey];
      opt.textContent = labelFn(it);
      select.appendChild(opt);
    });
  }
  if (movRefaccion) llenarSelect(movRefaccion, refacciones, "numeroregistro", function (r) { return r.nombre + " (stock: " + r.stock + ")"; });

  // Las piezas SI se filtran por la maquina de la orden abierta (la
  // refaccion se deja para despues, a proposito): refrescarSelectPiezas()
  // se vuelve a llamar cada vez que se abre el drawer de una orden, en
  // abrirDrawer(). "numeroserie" es el nombre real del campo en el modelo
  // Pieza -- antes decia "numeroeserie" (typo) y el select siempre quedaba
  // vacio de value.
  function refrescarSelectPiezas(maquinaCodigo) {
    if (!movPieza) return;
    var piezasMaquina = maquinaCodigo
      ? piezas.filter(function (p) { return p.maquina === maquinaCodigo; })
      : [];
    llenarSelect(movPieza, piezasMaquina, "numeroserie", function (p) { return p.nombre + " — " + p.numeroserie; });
  }

  function pintarMovPendientes() {
    if (!movList) return;
    movList.innerHTML = "";
    movPendientes.forEach(function (m, idx) {
      var row = document.createElement("div");
      row.className = "orden-mov__item";
      row.innerHTML = "<span>" + m.refaccionNombre + (m.piezaNombre ? " → reemplaza " + m.piezaNombre : "") + "</span>";
      var del = document.createElement("button");
      del.type = "button"; del.textContent = "×"; del.className = "orden-mov__item-del";
      del.addEventListener("click", function () { movPendientes.splice(idx, 1); pintarMovPendientes(); });
      row.appendChild(del);
      movList.appendChild(row);
    });
  }

  if (movAddBtn && movForm) {
    movAddBtn.addEventListener("click", function () { movForm.hidden = false; movAddBtn.hidden = true; });
  }
  if (movCancelar) {
    movCancelar.addEventListener("click", function () { movForm.hidden = true; movAddBtn.hidden = false; movRefaccion.value = ""; movPieza.value = ""; });
  }
  if (movConfirmar) {
    movConfirmar.addEventListener("click", function () {
      if (!movRefaccion.value) return;
      movPendientes.push({
        refaccion: movRefaccion.value,
        refaccionNombre: movRefaccion.options[movRefaccion.selectedIndex].textContent,
        pieza: movPieza.value || null,
        piezaNombre: movPieza.value ? movPieza.options[movPieza.selectedIndex].textContent : null,
      });
      pintarMovPendientes();
      movForm.hidden = true; movAddBtn.hidden = false; movRefaccion.value = ""; movPieza.value = "";
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
        // Cada renglon trae refaccion (obligatoria) y pieza (opcional, la
        // que salio de la maquina). El backend, dentro de la misma
        // transaccion que cierra la orden, emite un DESMO por cada pieza
        // retirada y un INSTA por cada refaccion instalada.
        movimientos: movPendientes.map(function (m) {
          return { refaccion: m.refaccion, pieza: m.pieza || null };
        }),
      };
      fetch(urlPara(CERRAR_TPL, folio), {
        method: "PATCH",
        headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
        body: JSON.stringify(payload),
      }).then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
        .then(function (res) {
          if (!res.ok) {
            mostrarMsg(typeof res.data === "object" ? JSON.stringify(res.data) : "No se pudo cerrar la orden.", false);
            return;
          }
          mostrarMsg("Orden cerrada. Indicadores actualizados.", true);
          movPendientes = []; pintarMovPendientes();
          cerrarDrawerPanel();
          cargarOrdenes();
        }).catch(function () { mostrarMsg("Sin conexión.", false); });
    });
  }

  cargarOrdenes();
})();