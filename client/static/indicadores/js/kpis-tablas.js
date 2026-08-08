(function () {
  "use strict";

  // Slug (el que usa la URL v1/kpi/<slug>/) -> titulo/sub para la tarjeta.
  // El orden aqui es el orden en que se pintan las tarjetas.
  var VISTAS = [
    { slug: "estado-flota", titulo: "Estado de la flota", sub: "Cuántas máquinas hay en cada estado operativo ahora mismo." },
    { slug: "indicadores-actuales", titulo: "Indicadores actuales", sub: "Tiempo medio de reparación (MTTR), tiempo medio entre fallas (MTBF) y disponibilidad, por máquina." },
    { slug: "disponibilidad-linea", titulo: "Disponibilidad por línea", sub: "Disponibilidad promedio de cada línea de producción a lo largo del tiempo." },
    { slug: "fallas-por-maquina", titulo: "Fallas por máquina", sub: "Total de fallas registradas por cada máquina." },
    { slug: "top-fallas", titulo: "Top fallas", sub: "Los tipos de falla que se repiten con más frecuencia." },
    { slug: "mantenimiento-por-maquina", titulo: "Mantenimiento por máquina", sub: "Órdenes de mantenimiento preventivo frente a correctivo." },
    { slug: "horas-operacion", titulo: "Horas de operación", sub: "Horas operadas por cada máquina y línea." },
    { slug: "reportes-atencion", titulo: "Reportes en atención", sub: "Reportes de falla que siguen abiertos o en proceso de atención." },
    { slug: "stock", titulo: "Stock de refacciones", sub: "Refacciones cuya existencia está en o por debajo de su mínimo." },
    { slug: "monitoreo-predictivo", titulo: "Monitoreo predictivo", sub: "Últimas lecturas y alertas del monitoreo de sensores." },
  ];

  var API_BASE = "/indicadores/";
  var MAX_FILAS_GRAFICA = 20; // no saturar el eje con demasiadas categorias

  // Estado en memoria por vista: datos ya descargados, modo actual (tabla/grafica)
  // e instancia de Chart.js viva (para poder destruirla antes de re-pintar).
  var DATOS = {};
  var MODO = {};
  var CHARTS = {};

  function cssVar(name, fallback) {
    var v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  }

  var COLOR_MUTED = cssVar("--color-muted", "#94a3b8");
  var COLOR_GRID = "rgba(148, 163, 184, 0.15)";
  var PALETA = [
    cssVar("--color-primary", "#38bdf8"),
    cssVar("--color-success", "#34d399"),
    cssVar("--color-danger", "#fb7185"),
    cssVar("--color-warning", "#fbbf24"),
    cssVar("--color-info", "#94a3b8"),
    cssVar("--color-secondary", "#64748b"),
  ];

  function fetchJSON(url) {
    return fetch(API_BASE + url).then(function (res) {
      if (!res.ok) throw new Error("Error " + res.status);
      return res.json();
    });
  }

  function etiquetaColumna(clave) {
    return clave
      .replace(/_/g, " ")
      .replace(/\b\w/g, function (c) { return c.toUpperCase(); });
  }

  function formatearValor(valor) {
    if (valor === null || valor === undefined || valor === "") return "—";
    if (typeof valor === "boolean") return valor ? "Sí" : "No";
    if (typeof valor === "number") {
      return Number.isInteger(valor) ? String(valor) : valor.toFixed(2);
    }
    // Fechas/datetimes ya vienen como ISO string (ver _filas_a_dicts en el api/).
    if (typeof valor === "string" && /^\d{4}-\d{2}-\d{2}/.test(valor)) {
      var d = new Date(valor);
      if (!isNaN(d.getTime())) {
        var soloFecha = valor.length <= 10;
        return soloFecha
          ? d.toLocaleDateString("es-MX")
          : d.toLocaleString("es-MX", { dateStyle: "medium", timeStyle: "short" });
      }
    }
    return String(valor);
  }

  // --- Tarjeta y controles -------------------------------------------------

  function crearTarjeta(vista) {
    var card = document.createElement("article");
    card.className = "kpi__panel kpi__vista-card";
    card.id = "vista-" + vista.slug;
    card.innerHTML =
      '<div class="kpi__panel-head">' +
        '<div>' +
          '<p class="kpi__panel-title">' + vista.titulo + '</p>' +
          '<p class="kpi__panel-sub">' + vista.sub + '</p>' +
        '</div>' +
        '<div class="kpi__vista-actions">' +
          '<span class="kpi__pill kpi__pill--modo">Tabla</span>' +
          '<button type="button" class="kpi__btn kpi__btn--ghost kpi__btn--expandir" title="Ampliar esta tarjeta">⤢ Expandir</button>' +
          '<button type="button" class="kpi__btn kpi__btn--ghost kpi__btn--grafica" disabled>Ver como gráfica</button>' +
        '</div>' +
      '</div>' +
      '<div class="kpi__table-wrap" data-vista="' + vista.slug + '"></div>';

    var btnExpandir = card.querySelector(".kpi__btn--expandir");
    btnExpandir.addEventListener("click", function () {
      var expandido = card.classList.toggle("kpi__vista-card--expanded");
      btnExpandir.textContent = expandido ? "⤡ Contraer" : "⤢ Expandir";
      // Si esta en modo grafica, Chart.js necesita que le avisen del resize
      // del contenedor (el toggle cambia el alto via CSS).
      if (CHARTS[vista.slug]) {
        setTimeout(function () { CHARTS[vista.slug].resize(); }, 260);
      }
      if (expandido) card.scrollIntoView({ behavior: "smooth", block: "start" });
    });

    var btnGrafica = card.querySelector(".kpi__btn--grafica");
    btnGrafica.addEventListener("click", function () {
      MODO[vista.slug] = MODO[vista.slug] === "grafica" ? "tabla" : "grafica";
      renderizarVista(vista.slug);
    });

    return card;
  }

  function actualizarControles(slug) {
    var card = document.getElementById("vista-" + slug);
    if (!card) return;
    var enGrafica = MODO[slug] === "grafica";
    var pill = card.querySelector(".kpi__pill--modo");
    var btnGrafica = card.querySelector(".kpi__btn--grafica");
    if (pill) pill.textContent = enGrafica ? "Gráfica" : "Tabla";
    if (btnGrafica) {
      btnGrafica.textContent = enGrafica ? "Ver como tabla" : "Ver como gráfica";
      btnGrafica.classList.toggle("is-active", enGrafica);
    }
  }

  // --- Estados vacios/errores ----------------------------------------------

  function pintarLoading(wrap) {
    wrap.innerHTML = '<div class="kpi__loading"><div class="kpi__spinner"></div></div>';
  }

  function pintarError(wrap) {
    wrap.innerHTML = '<div class="kpi__error">No se pudo cargar esta vista.</div>';
  }

  function pintarVacio(wrap) {
    wrap.innerHTML = '<p class="kpi__table-empty">Sin datos por ahora.</p>';
  }

  function pintarMensaje(wrap, texto) {
    wrap.innerHTML = '<p class="kpi__table-empty">' + texto + '</p>';
  }

  // --- Tabla ----------------------------------------------------------------

  function pintarTabla(wrap, filas) {
    if (!filas || !filas.length) {
      pintarVacio(wrap);
      return;
    }
    var columnas = Object.keys(filas[0]);

    var table = document.createElement("table");
    table.className = "kpi__table";

    var thead = document.createElement("thead");
    var trHead = document.createElement("tr");
    columnas.forEach(function (col) {
      var th = document.createElement("th");
      th.textContent = etiquetaColumna(col);
      trHead.appendChild(th);
    });
    thead.appendChild(trHead);

    var tbody = document.createElement("tbody");
    filas.forEach(function (fila) {
      var tr = document.createElement("tr");
      columnas.forEach(function (col) {
        var td = document.createElement("td");
        td.textContent = formatearValor(fila[col]);
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });

    table.appendChild(thead);
    table.appendChild(tbody);

    wrap.innerHTML = "";
    var scroll = document.createElement("div");
    scroll.className = "kpi__table-scroll";
    scroll.appendChild(table);
    wrap.appendChild(scroll);
  }

  // --- Grafica (generica: la arma sola a partir de las columnas) -----------

  // Primera columna = etiqueta/categoria. El resto de columnas donde TODOS
  // los valores son numero (o null) se toman como series a graficar.
  function detectarSeries(columnas, filas) {
    var colEtiqueta = columnas[0];
    var colsNumericas = columnas.slice(1).filter(function (col) {
      return filas.every(function (f) { return typeof f[col] === "number" || f[col] === null; });
    });
    return { colEtiqueta: colEtiqueta, colsNumericas: colsNumericas };
  }

  function pintarGrafica(wrap, filas, vista) {
    if (typeof Chart === "undefined") {
      pintarMensaje(wrap, "No se pudo cargar Chart.js (sin conexión).");
      return;
    }
    if (!filas || !filas.length) {
      pintarVacio(wrap);
      return;
    }

    var columnas = Object.keys(filas[0]);
    var series = detectarSeries(columnas, filas);

    if (!series.colsNumericas.length) {
      pintarMensaje(wrap, "Esta vista no tiene columnas numéricas para graficar. Usa la tabla.");
      return;
    }

    // Si hay muchas filas, nos quedamos con las de mayor valor en la
    // primera serie numerica, para que la grafica siga siendo legible.
    var datos = filas.slice();
    var truncado = datos.length > MAX_FILAS_GRAFICA;
    if (truncado) {
      var colOrden = series.colsNumericas[0];
      datos.sort(function (a, b) { return (b[colOrden] || 0) - (a[colOrden] || 0); });
      datos = datos.slice(0, MAX_FILAS_GRAFICA);
    }

    var labels = datos.map(function (f) { return String(f[series.colEtiqueta] != null ? f[series.colEtiqueta] : "—"); });
    var datasets = series.colsNumericas.map(function (col, i) {
      return {
        label: etiquetaColumna(col),
        data: datos.map(function (f) { return f[col] || 0; }),
        backgroundColor: PALETA[i % PALETA.length],
        borderRadius: 5,
      };
    });

    wrap.innerHTML = "";
    var canvasWrap = document.createElement("div");
    canvasWrap.className = "kpi__vista-canvas-wrap";
    var canvas = document.createElement("canvas");
    canvasWrap.appendChild(canvas);
    wrap.appendChild(canvasWrap);

    if (truncado) {
      var nota = document.createElement("p");
      nota.className = "kpi__table-empty";
      nota.style.fontSize = "0.72rem";
      nota.textContent = "Mostrando las " + MAX_FILAS_GRAFICA + " filas con mayor valor, de " + filas.length + " en total.";
      wrap.appendChild(nota);
    }

    if (CHARTS[vista.slug]) {
      CHARTS[vista.slug].destroy();
    }

    var soloUnaSerie = datasets.length === 1;
    CHARTS[vista.slug] = new Chart(canvas, {
      type: "bar",
      data: { labels: labels, datasets: datasets },
      options: {
        indexAxis: soloUnaSerie ? "y" : "x",
        responsive: true,
        maintainAspectRatio: false,
        color: COLOR_MUTED,
        plugins: {
          legend: { display: !soloUnaSerie, labels: { boxWidth: 12, boxHeight: 12, padding: 12, color: COLOR_MUTED } },
        },
        scales: {
          x: { ticks: { color: COLOR_MUTED }, grid: { color: COLOR_GRID } },
          y: { beginAtZero: true, ticks: { color: COLOR_MUTED, precision: 0 }, grid: { color: COLOR_GRID } },
        },
      },
    });
  }

  // --- Orquestacion -----------------------------------------------------

  function renderizarVista(slug) {
    var wrap = document.querySelector('.kpi__table-wrap[data-vista="' + slug + '"]');
    if (!wrap) return;
    actualizarControles(slug);
    var filas = DATOS[slug];
    if (filas === undefined) return; // aun cargando
    if (MODO[slug] === "grafica") {
      var vista = VISTAS.filter(function (v) { return v.slug === slug; })[0];
      pintarGrafica(wrap, filas, vista);
    } else {
      pintarTabla(wrap, filas);
    }
  }

  function cargarVista(vista) {
    var wrap = document.querySelector('.kpi__table-wrap[data-vista="' + vista.slug + '"]');
    var card = document.getElementById("vista-" + vista.slug);
    if (!wrap) return;
    pintarLoading(wrap);
    fetchJSON("v1/kpi/" + vista.slug + "/")
      .then(function (data) {
        DATOS[vista.slug] = data;
        var btnGrafica = card && card.querySelector(".kpi__btn--grafica");
        if (btnGrafica) btnGrafica.disabled = false;
        renderizarVista(vista.slug);
      })
      .catch(function () { pintarError(wrap); });
  }

  function cargarTodo() {
    VISTAS.forEach(cargarVista);
  }

  function aplicarFiltro(texto) {
    var q = texto.trim().toLowerCase();
    document.querySelectorAll(".kpi__vista-card").forEach(function (card) {
      var filas = card.querySelectorAll(".kpi__table tbody tr");
      var visibles = 0;
      filas.forEach(function (tr) {
        var coincide = !q || tr.textContent.toLowerCase().indexOf(q) !== -1;
        tr.style.display = coincide ? "" : "none";
        if (coincide) visibles++;
      });
      // Solo oculta la tarjeta completa si tiene filas pero ninguna coincide.
      // (En modo grafica no hay filas de tabla que contar, asi que no se oculta.)
      card.style.display = (q && filas.length && visibles === 0) ? "none" : "";
    });
  }

  function initReporteModal() {
    var modal = document.getElementById("kpiModalReporte");
    var abrirReporte = document.getElementById("kpiAbrirReporte");
    var filtroPeriodo = document.getElementById("kpiFiltroPeriodo");
    var fechaInicioWrap = document.getElementById("kpiFiltroFechaInicioWrap");
    var fechaFinWrap = document.getElementById("kpiFiltroFechaFinWrap");
    var fechaInicioInput = document.getElementById("kpiFiltroFechaInicio");
    var fechaFinInput = document.getElementById("kpiFiltroFechaFin");
    var checkTodas = document.getElementById("kpiCheckTodas");
    var listaVistas = document.getElementById("kpiListaVistas");
    var cerrarModal = modal.querySelectorAll("[data-kpi-cerrar-modal]");

    // Manejar cambio de periodo (presets + rango personalizado)
    filtroPeriodo.addEventListener("change", function () {
      var valor = filtroPeriodo.value;
      var hoy = new Date();
      var fechaInicio = new Date();
      var fechaFin = new Date();

      fechaInicioWrap.hidden = valor !== "custom";
      fechaFinWrap.hidden = valor !== "custom";

      if (valor === "7") {
        fechaInicio.setDate(hoy.getDate() - 7);
      } else if (valor === "30") {
        fechaInicio.setDate(hoy.getDate() - 30);
      } else if (valor === "90") {
        fechaInicio.setDate(hoy.getDate() - 90);
      } else if (valor === "365") {
        fechaInicio.setDate(hoy.getDate() - 365);
      }

      if (valor !== "custom" && valor !== "") {
        fechaInicioInput.value = fechaInicio.toISOString().split("T")[0];
        fechaFinInput.value = fechaFin.toISOString().split("T")[0];
      }
    });

    // Inicializar fechas con el preset de 30 días
    filtroPeriodo.value = "30";
    filtroPeriodo.dispatchEvent(new Event("change"));

    // Checkbox "Seleccionar todas"
    checkTodas.addEventListener("change", function () {
      var checks = listaVistas.querySelectorAll("input[type='checkbox']");
      checks.forEach(function (check) {
        check.checked = checkTodas.checked;
      });
    });

    // Lista de vistas (checkboxes)
    VISTAS.forEach(function (vista) {
      var li = document.createElement("li");
      var check = document.createElement("input");
      check.type = "checkbox";
      check.id = "check-" + vista.slug;
      check.value = vista.slug;
      check.checked = true;
      check.addEventListener("change", function () {
        var checks = listaVistas.querySelectorAll("input[type='checkbox']:checked");
        checkTodas.checked = checks.length === VISTAS.length;
      });

      var label = document.createElement("label");
      label.htmlFor = check.id;
      label.textContent = vista.titulo;

      li.appendChild(check);
      li.appendChild(label);
      listaVistas.appendChild(li);
    });

    // Botones de descarga
    modal.querySelectorAll(".kpi__modal-foot .kpi__btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var formato = btn.dataset.formato;
        var vistasSeleccionadas = Array.from(listaVistas.querySelectorAll("input[type='checkbox']:checked")).map(function (check) {
          return check.value;
        }).join(",");

        var params = new URLSearchParams();
        params.append("vistas", vistasSeleccionadas);

        if (filtroPeriodo.value === "custom") {
          if (fechaInicioInput.value) params.append("fecha_inicio", fechaInicioInput.value);
          if (fechaFinInput.value) params.append("fecha_fin", fechaFinInput.value);
        } else if (filtroPeriodo.value) {
          var dias = parseInt(filtroPeriodo.value);
          var fechaInicio = new Date();
          fechaInicio.setDate(fechaInicio.getDate() - dias);
          params.append("fecha_inicio", fechaInicio.toISOString().split("T")[0]);
          params.append("fecha_fin", new Date().toISOString().split("T")[0]);
        }

        var url = API_BASE + "v1/reporte/export/" + formato + "/?" + params.toString();
        window.location.href = url;
        modal.classList.remove("is-open");
      });
    });

    // Abrir/cerrar modal
    abrirReporte.addEventListener("click", function () {
      modal.classList.add("is-open");
    });

    cerrarModal.forEach(function (btn) {
      btn.addEventListener("click", function () {
        modal.classList.remove("is-open");
      });
    });
  }

  function init() {
    var grid = document.getElementById("kpiVistaGrid");
    if (!grid) return;

    VISTAS.forEach(function (vista) {
      grid.appendChild(crearTarjeta(vista));
    });

    cargarTodo();

    var recargar = document.getElementById("kpiRecargarTodo");
    if (recargar) recargar.addEventListener("click", cargarTodo);

    var filtro = document.getElementById("kpiFiltroTablas");
    if (filtro) filtro.addEventListener("input", function () { aplicarFiltro(filtro.value); });

    initReporteModal();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
