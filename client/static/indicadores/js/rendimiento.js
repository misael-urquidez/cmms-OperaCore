(function () {
  "use strict";

  var API_BASE = "/indicadores/";

  function fetchJSON(url) {
    return fetch(API_BASE + url).then(function (res) {
      if (!res.ok) throw new Error("Error " + res.status);
      return res.json();
    });
  }

  function claseBadge(pct) {
    if (pct >= 80) return "kpi__badge--ok";
    if (pct >= 50) return "kpi__badge--warn";
    return "kpi__badge--bad";
  }

  function pintarCards(data) {
    var wrap = document.getElementById("rendimientoCards");
    if (!wrap) return;

    var total = data.length;
    var asignadas = data.reduce(function (a, d) { return a + d.OrdenesAsignadas; }, 0);
    var cerradas = data.reduce(function (a, d) { return a + d.OrdenesCerradas; }, 0);
    var promedio = asignadas ? Math.round((cerradas / asignadas) * 1000) / 10 : 0;

    wrap.innerHTML =
      '<article class="stat-card">' +
        '<span class="stat-card__icon stat-card__icon--sky"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg></span>' +
        '<div><p class="stat-card__label">Trabajadores evaluados</p><p class="stat-card__value">' + total + '</p></div>' +
      '</article>' +
      '<article class="stat-card">' +
        '<span class="stat-card__icon stat-card__icon--amber"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M8 2v4M16 2v4"/></svg></span>' +
        '<div><p class="stat-card__label">Órdenes asignadas</p><p class="stat-card__value">' + asignadas + '</p></div>' +
      '</article>' +
      '<article class="stat-card">' +
        '<span class="stat-card__icon stat-card__icon--green"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6 9 17l-5-5"/></svg></span>' +
        '<div><p class="stat-card__label">Órdenes cerradas</p><p class="stat-card__value">' + cerradas + '</p></div>' +
      '</article>' +
      '<article class="stat-card">' +
        '<span class="stat-card__icon stat-card__icon--rose"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 8v4l3 3M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"/></svg></span>' +
        '<div><p class="stat-card__label">% de cierre promedio</p><p class="stat-card__value">' + promedio + '%</p></div>' +
      '</article>';
  }

  function pintarTabla(data) {
    var wrap = document.getElementById("rendimientoTabla");
    if (!wrap) return;

    if (!data.length) {
      wrap.innerHTML = '<p class="kpi__table-empty">No hay trabajadores registrados.</p>';
      return;
    }

    var table = document.createElement("table");
    table.className = "kpi__table";
    table.innerHTML =
      '<thead><tr>' +
        '<th>Nómina</th><th>Trabajador</th><th>Asignadas</th><th>Cerradas</th>' +
        '<th>Pendientes</th><th>% Cierre</th>' +
      '</tr></thead>';

    var tbody = document.createElement("tbody");
    data.forEach(function (fila) {
      var tr = document.createElement("tr");
      tr.dataset.filtro = (fila.numeroNomina + " " + fila.Nombre).toLowerCase();
      tr.innerHTML =
        '<td>' + fila.numeroNomina + '</td>' +
        '<td>' + fila.Nombre + '</td>' +
        '<td>' + fila.OrdenesAsignadas + '</td>' +
        '<td>' + fila.OrdenesCerradas + '</td>' +
        '<td>' + fila.OrdenesPendientes + '</td>' +
        '<td>' +
          '<div class="kpi__bar"><div class="kpi__bar-fill" style="width:' + fila.PorcentajeCierre + '%"></div></div> ' +
          '<span class="kpi__badge ' + claseBadge(fila.PorcentajeCierre) + '">' + fila.PorcentajeCierre + '%</span>' +
        '</td>';
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);

    wrap.innerHTML = "";
    var scroll = document.createElement("div");
    scroll.className = "kpi__table-scroll";
    scroll.appendChild(table);
    wrap.appendChild(scroll);
  }

  function cargar() {
    var wrap = document.getElementById("rendimientoTabla");
    if (wrap) wrap.innerHTML = '<div class="kpi__loading"><div class="kpi__spinner"></div></div>';
    fetchJSON("v1/rendimiento-trabajadores/")
      .then(function (data) {
        pintarCards(data);
        pintarTabla(data);
      })
      .catch(function () {
        if (wrap) wrap.innerHTML = '<div class="kpi__error">No se pudo cargar el rendimiento.</div>';
      });
  }

  function aplicarFiltro(texto) {
    var q = texto.trim().toLowerCase();
    document.querySelectorAll("#rendimientoTabla tbody tr").forEach(function (tr) {
      tr.style.display = (!q || tr.dataset.filtro.indexOf(q) !== -1) ? "" : "none";
    });
  }

  function init() {
    if (!document.getElementById("rendimientoTabla")) return;
    cargar();

    var recargar = document.getElementById("rendimientoRecargar");
    if (recargar) recargar.addEventListener("click", cargar);

    var filtro = document.getElementById("rendimientoFiltro");
    if (filtro) filtro.addEventListener("input", function () { aplicarFiltro(filtro.value); });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();