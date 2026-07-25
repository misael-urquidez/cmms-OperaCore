(function () {
  "use strict";

  var root = document.querySelector(".ordenes");
  if (!root) return;

  var DATOS_URL = root.dataset.datosUrl;
  var CREAR_URL = root.dataset.crearUrl;
  var ASIGNAR_TPL = root.dataset.asignarUrlBase;
  var INICIAR_TPL = root.dataset.iniciarUrlBase;
  var CERRAR_TPL = root.dataset.cerrarUrlBase;
  var ES_TECNICO = root.dataset.esTecnico === "1";
  var NUMERO_NOMINA = root.dataset.numeroNomina;

  var trabajadoresEl = document.getElementById("trabajadores-data");
  var maquinasEl = document.getElementById("maquinas-data");
  var trabajadores = trabajadoresEl ? JSON.parse(trabajadoresEl.textContent || "[]") : [];
  var maquinas = maquinasEl ? JSON.parse(maquinasEl.textContent || "[]") : [];

  var listEl = document.getElementById("ordenesList");
  var emptyEl = document.getElementById("ordenesEmpty");
  var filtroEstado = document.getElementById("filtroEstado");

  var estado = { ordenes: [], seleccionada: null };

  var _modalNuevaOrden = document.getElementById("newOrdenModal");
  var _drawerOrden = document.getElementById("ordenDrawer");
  if (_modalNuevaOrden) conBloqueoScroll(_modalNuevaOrden);
  if (_drawerOrden) conBloqueoScroll(_drawerOrden);

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
    function cerrarModal() { modal.close(); form.reset(); }

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

    drawer.showModal();
  }

  var btnCerrarDrawer = document.getElementById("ordenDrawerClose");
  if (btnCerrarDrawer) btnCerrarDrawer.addEventListener("click", function () { drawer.close(); estado.seleccionada = null; });

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
          drawer.close();
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
          drawer.close();
          cargarOrdenes();
        }).catch(function () { mostrarMsg("Sin conexión.", false); });
    });
  }

  if (formCerrar) {
    formCerrar.addEventListener("submit", function (ev) {
      ev.preventDefault();
      if (!estado.seleccionada) return;
      var payload = {
        diagnostico: document.getElementById("cDiagnostico").value,
        notas: document.getElementById("cNotas").value,
        horasIntervenidas: parseFloat(document.getElementById("cHoras").value),
      };
      fetch(urlPara(CERRAR_TPL, estado.seleccionada.folio), {
        method: "PATCH",
        headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
        body: JSON.stringify(payload),
      }).then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
        .then(function (res) {
          if (!res.ok) { mostrarMsg("No se pudo cerrar la orden.", false); return; }
          mostrarMsg("Orden cerrada. Indicadores actualizados.", true);
          drawer.close();
          cargarOrdenes();
        }).catch(function () { mostrarMsg("Sin conexión.", false); });
    });
  }

  cargarOrdenes();
})();