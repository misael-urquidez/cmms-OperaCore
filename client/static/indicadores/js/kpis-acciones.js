(function () {
  "use strict";

  var API_BASE = "/indicadores/";

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

  function fetchConEstado(url, opciones) {
    return fetch(url, opciones).then(function (res) {
      return res.json().then(function (data) {
        return { ok: res.ok, status: res.status, data: data };
      });
    });
  }

  // ============================================================
  // Cerrar periodo (sp_cerrar_periodo_indicador)
  // ============================================================

  function cargarMaquinas(select) {
    select.innerHTML = '<option value="">Cargando máquinas…</option>';
    fetch(API_BASE + "v1/kpi/indicadores-actuales/")
      .then(function (res) { return res.json(); })
      .then(function (filas) {
        select.innerHTML = "";
        if (!filas || !filas.length) {
          var vacio = document.createElement("option");
          vacio.textContent = "Sin máquinas disponibles";
          select.appendChild(vacio);
          return;
        }
        filas.forEach(function (fila) {
          var opt = document.createElement("option");
          opt.value = fila.Codigo;
          opt.textContent = fila.Maquina + " (" + fila.Codigo + ")";
          select.appendChild(opt);
        });
      })
      .catch(function () {
        select.innerHTML = '<option value="">Error al cargar máquinas</option>';
      });
  }

  function initCerrarPeriodo() {
    var modal = document.getElementById("kpiModalCerrarPeriodo");
    if (!modal) return;

    var abrir = document.getElementById("quickAddCerrarPeriodo");

    var select = document.getElementById("cerrarPeriodoMaquina");
    var fechaInput = document.getElementById("cerrarPeriodoFecha");
    var msg = document.getElementById("cerrarPeriodoMsg");
    var confirmar = document.getElementById("cerrarPeriodoConfirmar");
    var cerrarBtns = modal.querySelectorAll("[data-kpi-cerrar-modal-periodo]");

    function abrirModal() {
      cargarMaquinas(select);
      fechaInput.value = "";
      msg.textContent = "";
      modal.classList.add("is-open");
      var quickAddMenu = document.getElementById("quickAddMenu");
      var quickAddBtn = document.getElementById("quickAddBtn");
      if (quickAddMenu) quickAddMenu.classList.remove("is-open");
      if (quickAddBtn) quickAddBtn.setAttribute("aria-expanded", "false");
    }

    if (abrir) {
      abrir.addEventListener("click", function (e) {
        if (abrir.tagName === "BUTTON") e.preventDefault();
        abrirModal();
      });
    }

    if (new URLSearchParams(window.location.search).get("accion") === "cerrar-periodo") {
      abrirModal();
      var url = new URL(window.location.href);
      url.searchParams.delete("accion");
      window.history.replaceState({}, "", url);
    }

    cerrarBtns.forEach(function (btn) {
      btn.addEventListener("click", function () { modal.classList.remove("is-open"); });
    });

    confirmar.addEventListener("click", function () {
      var maquina = select.value;
      var fecha = fechaInput.value;
      if (!maquina || !fecha) {
        msg.textContent = "Elige una máquina y una fecha de cierre.";
        return;
      }

      confirmar.disabled = true;
      msg.textContent = "Cerrando periodo…";

      fetchConEstado(API_BASE + "v2/cerrar-periodo/", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
        body: JSON.stringify({ maquina: maquina, fecha_fin: fecha }),
      })
        .then(function (res) {
          confirmar.disabled = false;
          if (!res.ok) {
            msg.textContent = (res.data && res.data.detail) || "No se pudo cerrar el periodo.";
            return;
          }
          msg.textContent = "Periodo cerrado y nuevo periodo abierto.";
          setTimeout(function () {
            modal.classList.remove("is-open");
            var recargar = document.getElementById("kpiRecargarTodo");
            if (recargar) recargar.click();
          }, 900);
        })
        .catch(function () {
          confirmar.disabled = false;
          msg.textContent = "Sin conexión con el servidor.";
        });
    });
  }

  // ============================================================
  // Reporte de disponibilidad por rango (sp_reporte_disponibilidad_planta)
  // ============================================================

  function etiquetaColumna(clave) {
    return clave
      .replace(/_/g, " ")
      .replace(/\b\w/g, function (c) { return c.toUpperCase(); });
  }

  function pintarTablaReporte(wrap, filas) {
    if (!filas || !filas.length) {
      wrap.innerHTML = '<p class="kpi__table-empty">Sin datos para ese rango.</p>';
      return;
    }
    var columnas = Object.keys(filas[0]);
    var html = '<div class="kpi__table-scroll"><table class="kpi__table"><thead><tr>';
    columnas.forEach(function (c) { html += "<th>" + etiquetaColumna(c) + "</th>"; });
    html += "</tr></thead><tbody>";
    filas.forEach(function (fila) {
      html += "<tr>";
      columnas.forEach(function (c) {
        var v = fila[c];
        html += "<td>" + (v === null || v === undefined || v === "" ? "—" : v) + "</td>";
      });
      html += "</tr>";
    });
    html += "</tbody></table></div>";
    wrap.innerHTML = html;
  }

  window.kpiReporteDispoRango = { fechaInicio: null, fechaFin: null, generado: false };

  function initReporteDisponibilidad() {
    var boton = document.getElementById("reporteDispoGenerar");
    var wrap = document.getElementById("reporteDispoResultado");
    var inicio = document.getElementById("reporteDispoFechaInicio");
    var fin = document.getElementById("reporteDispoFechaFin");
    if (!boton || !wrap) return;

    boton.addEventListener("click", function () {
      if (!inicio.value || !fin.value) {
        wrap.innerHTML = '<p class="kpi__table-empty">Elige el rango de fechas.</p>';
        return;
      }
      wrap.innerHTML = '<div class="kpi__loading"><div class="kpi__spinner"></div></div>';

      var params = new URLSearchParams({ fecha_inicio: inicio.value, fecha_fin: fin.value });
      fetchConEstado(API_BASE + "v1/reporte-disponibilidad/?" + params.toString())
        .then(function (res) {
          if (!res.ok) {
            wrap.innerHTML = '<div class="kpi__error">' +
              ((res.data && res.data.detail) || "No se pudo generar el reporte.") + "</div>";
            window.kpiReporteDispoRango.generado = false;
            return;
          }
          pintarTablaReporte(wrap, res.data);
          window.kpiReporteDispoRango = { fechaInicio: inicio.value, fechaFin: fin.value, generado: true };
        })
        .catch(function () {
          wrap.innerHTML = '<div class="kpi__error">Sin conexión con el servidor.</div>';
          window.kpiReporteDispoRango.generado = false;
        });
    });
  }

  function init() {
    initCerrarPeriodo();
    initReporteDisponibilidad();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
