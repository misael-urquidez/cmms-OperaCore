(function () {
  "use strict";

  var root = document.getElementById("ordenTrabajo");
  if (!root) return;

  var INICIAR_URL = root.dataset.iniciarUrl;
  var CERRAR_URL = root.dataset.cerrarUrl;

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

  function mostrarMsg(texto, ok) {
    var el = document.getElementById("ordenTrabajoMsg");
    if (!el) return;
    el.textContent = texto;
    el.className = ok ? "ok" : "error";
  }

  // ---------------------------------------------------- marcar en progreso
  var btnIniciar = document.getElementById("ordenTrabajoIniciarBtn");
  if (btnIniciar) {
    btnIniciar.addEventListener("click", function () {
      btnIniciar.disabled = true;
      fetch(INICIAR_URL, {
        method: "PATCH",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
      }).then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
        .then(function (res) {
          if (!res.ok) {
            mostrarMsg("No se pudo actualizar.", false);
            btnIniciar.disabled = false;
            return;
          }
          // Recargamos: el servidor ahora va a renderizar puede_cerrar=True
          // y aparece el formulario de diagnostico/notas/horas/piezas.
          window.location.reload();
        }).catch(function () {
          mostrarMsg("Sin conexión.", false);
          btnIniciar.disabled = false;
        });
    });
  }

  // ---------------------------------------------------- piezas / refacciones
  var piezasEl = document.getElementById("orden-trabajo-piezas-data");
  var refaccionesEl = document.getElementById("orden-trabajo-refacciones-data");
  var piezas = piezasEl ? JSON.parse(piezasEl.textContent || "[]") : [];
  var refacciones = refaccionesEl ? JSON.parse(refaccionesEl.textContent || "[]") : [];

  var movPendientes = []; // [{refaccion, refaccionNombre, pieza, piezaNombre}]
  var movList = document.getElementById("ordenMovList");
  var movAddBtn = document.getElementById("ordenMovAddBtn");
  var movForm = document.getElementById("ordenMovForm");
  var movRefaccion = document.getElementById("ordenMovRefaccion");
  var movPieza = document.getElementById("ordenMovPieza");
  var movConfirmar = document.getElementById("ordenMovConfirmar");
  var movCancelar = document.getElementById("ordenMovCancelar");
  var movError = document.getElementById("ordenMovError");

  function limpiarMovError() { if (movError) movError.hidden = true; }
  function mostrarMovError() { if (movError) movError.hidden = false; }

  function llenarSelect(select, items, valueKey, labelFn) {
    if (!select) return;
    select.querySelectorAll("option:not(:first-child)").forEach(function (o) { o.remove(); });
    items.forEach(function (it) {
      var opt = document.createElement("option");
      opt.value = it[valueKey];
      opt.textContent = labelFn(it);
      select.appendChild(opt);
    });
  }
  // "numeroserie" es el nombre real del campo en el modelo Pieza.
  llenarSelect(movRefaccion, refacciones, "numeroregistro", function (r) { return r.nombre + " (stock: " + r.stock + ")"; });
  llenarSelect(movPieza, piezas, "numeroserie", function (p) { return p.nombre + " — " + p.numeroserie; });

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
    if (movAddBtn) movAddBtn.textContent = movPendientes.length ? "+ Agregar otra pieza" : "+ Agregar pieza";
  }

  if (movAddBtn && movForm) {
    movAddBtn.addEventListener("click", function () { movForm.hidden = false; movAddBtn.hidden = true; limpiarMovError(); });
  }
  if (movCancelar) {
    movCancelar.addEventListener("click", function () {
      movForm.hidden = true; movAddBtn.hidden = false; movRefaccion.value = ""; movPieza.value = ""; limpiarMovError();
    });
  }
  if (movConfirmar) {
    movConfirmar.addEventListener("click", function () {
      if (!movRefaccion.value) { mostrarMovError(); return; }
      limpiarMovError();
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

  // ---------------------------------------------------- cerrar orden
  var form = document.getElementById("ordenTrabajoForm");
  if (form) {
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var payload = {
        diagnostico: document.getElementById("twDiagnostico").value,
        notas: document.getElementById("twNotas").value,
        horasIntervenidas: parseFloat(document.getElementById("twHoras").value),
        movimientos: movPendientes.map(function (m) {
          return { refaccion: m.refaccion, pieza: m.pieza || null };
        }),
      };
      fetch(CERRAR_URL, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
        body: JSON.stringify(payload),
      }).then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
        .then(function (res) {
          if (!res.ok) {
            mostrarMsg(typeof res.data === "object" ? JSON.stringify(res.data) : "No se pudo cerrar la orden.", false);
            return;
          }
          // Recargamos: el servidor ahora renderiza la orden como cerrada,
          // con diagnostico/notas visibles igual que en cualquier otra
          // orden cerrada (misma vista que ya conoces).
          window.location.reload();
        }).catch(function () { mostrarMsg("Sin conexión.", false); });
    });
  }
})();