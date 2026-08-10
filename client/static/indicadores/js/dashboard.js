(function () {
  "use strict";

  if (typeof Chart === "undefined") {
    document.querySelectorAll(".kpi__canvas-wrap").forEach(function (wrap) {
      var msg = document.createElement("p");
      msg.className = "kpi__chart-fallback";
      msg.textContent = "No se pudo cargar Chart.js (sin conexión).";
      wrap.appendChild(msg);
    });
    return;
  }

  function cssVar(name, fallback) {
    var v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  }

  var COLOR_MUTED = cssVar("--color-muted", "#94a3b8");
  var COLOR_GRID = "rgba(148, 163, 184, 0.15)";
  var COLOR_PRIMARY = cssVar("--color-primary", "#38bdf8");
  var COLOR_SUCCESS = cssVar("--color-success", "#34d399");
  var COLOR_DANGER = cssVar("--color-danger", "#fb7185");
  var COLOR_WARNING = cssVar("--color-warning", "#fbbf24");
  var COLOR_INFO = cssVar("--color-info", "#94a3b8");
  var COLOR_SECONDARY = cssVar("--color-secondary", "#64748b");

  Chart.defaults.color = COLOR_MUTED;
  Chart.defaults.borderColor = COLOR_GRID;
  Chart.defaults.font.family = "'Segoe UI', system-ui, sans-serif";

  var PALETA_ESTADOS = [COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_INFO, COLOR_SECONDARY];
  var API_BASE = "/indicadores/";

  // Mapa de badges por el TEXTO exacto que trae EDO_MAQUINA.nombre / v_kpi_indicadores_actuales.Estado
  var BADGE_POR_ESTADO = {
    "operativa": "kpi__badge--ok",
    "en falla": "kpi__badge--bad",
    "en mantenimiento": "kpi__badge--warn",
    "en espera": "kpi__badge--info",
    "deshabilitada": "kpi__badge--info",
  };

  function showError(element, message) {
    if (!element) return;
    element.innerHTML = '<div class="kpi__error">' + (message || 'Error al cargar datos') + '</div>';
  }

  async function fetchData(url) {
    const response = await fetch(API_BASE + url);
    if (!response.ok) {
      throw new Error('Error ' + response.status + ' en ' + url);
    }
    return await response.json();
  }

  function setCard(index, value) {
    const el = document.querySelector('.stat-card:nth-child(' + index + ') .stat-card__value');
    if (el) el.textContent = (value === undefined || value === null) ? '0' : String(value);
  }

  // ── 1. Estado de la flota + tarjetas 1-3 (Operativas / En falla / En mantenimiento) ──
  async function cargarEstadoFlota() {
    const filas = await fetchData('v1/kpi/estado-flota/'); // [{Estado, Total}, ...]

    const porEstado = {};
    let total = 0;
    filas.forEach(f => {
      porEstado[(f.Estado || '').toLowerCase()] = f.Total;
      total += f.Total || 0;
    });

    setCard(1, porEstado['operativa'] || 0);
    document.querySelector('.stat-card:nth-child(1) .stat-card__hint').textContent = 'de ' + total + ' máquinas';
    setCard(2, porEstado['en falla'] || 0);
    setCard(3, porEstado['en mantenimiento'] || 0);

    new Chart(document.getElementById("chartFlota"), {
      type: "doughnut",
      data: {
        labels: filas.map(f => f.Estado),
        datasets: [{
          data: filas.map(f => f.Total),
          backgroundColor: PALETA_ESTADOS,
          borderWidth: 0,
          hoverOffset: 6,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "62%",
        plugins: {
          legend: { position: "right", labels: { boxWidth: 12, boxHeight: 12, padding: 12 } },
          tooltip: { callbacks: { label: ctx => " " + ctx.label + ": " + ctx.parsed + " máq." } },
        },
      },
    });
  }

  // ── 2. Tarjetas 4-5 (Fallas abiertas / Órdenes activas) ──
  async function cargarReportesAtencion() {
    const filas = await fetchData('v1/kpi/reportes-atencion/'); // [{FallasAbiertas, OrdenesActivas, OrdenesEnProgreso}]
    const r = filas[0] || {};
    setCard(4, r.FallasAbiertas || 0);
    setCard(5, r.OrdenesActivas || 0);
  }

  // ── 3. Tarjeta 6 (Refacciones bajo stock) ──
  async function cargarStock() {
    const filas = await fetchData('v1/kpi/stock/'); // [{Refaccion, SKU, Stock, StockMinimo, Faltantes, Criticidad}, ...]
    setCard(6, filas.length);
  }

  // ── 4. Top máquinas con más fallas ──
  async function cargarFallasPorMaquina() {
    const filas = await fetchData('v1/kpi/fallas-por-maquina/'); // [{Codigo, Maquina, TotalFallas}, ...]
    const top5 = [...filas].sort((a, b) => (b.TotalFallas || 0) - (a.TotalFallas || 0)).slice(0, 5);

    new Chart(document.getElementById("chartFallas"), {
      type: "bar",
      data: {
        labels: top5.map(f => f.Maquina || f.Codigo),
        datasets: [{
          data: top5.map(f => f.TotalFallas || 0),
          backgroundColor: COLOR_PRIMARY,
          borderRadius: 6,
        }],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: ctx => " " + ctx.parsed.x + " fallas" } },
        },
        scales: { x: { beginAtZero: true, ticks: { precision: 0 } } },
      },
    });
  }

  // ── 5. Mantenimiento por línea ──
  async function cargarMantenimientoPorLinea() {
    const filas = await fetchData('v1/kpi/mantenimiento-por-maquina/'); // [{Linea, Preventivos, Correctivos, Total}, ...]

    new Chart(document.getElementById("chartMantenimiento"), {
      type: "bar",
      data: {
        labels: filas.map(f => f.Linea || 'Sin línea'),
        datasets: [
          { label: "Preventivo", data: filas.map(f => f.Preventivos || 0), backgroundColor: COLOR_PRIMARY, borderRadius: 6 },
          { label: "Correctivo", data: filas.map(f => f.Correctivos || 0), backgroundColor: COLOR_DANGER, borderRadius: 6 },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "top", labels: { boxWidth: 12, boxHeight: 12, padding: 12 } } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
      },
    });
  }

  // ── 6. Disponibilidad de la planta (promedio entre líneas, por periodo) ──
  async function cargarDisponibilidad() {
    const filas = await fetchData('v1/kpi/disponibilidad-linea/'); // [{Linea, Periodo, Disponibilidad}, ...] -- 1 fila por linea+periodo

    const porPeriodo = {};
    filas.forEach(f => {
      if (!f.Periodo) return; // periodo abierto (fechaFin NULL) -> sin punto todavia
      if (!porPeriodo[f.Periodo]) porPeriodo[f.Periodo] = [];
      porPeriodo[f.Periodo].push(f.Disponibilidad || 0);
    });

    const periodos = Object.keys(porPeriodo).sort().slice(-6); // últimos 6 periodos
    const promedios = periodos.map(p => {
      const vals = porPeriodo[p];
      return vals.reduce((a, b) => a + b, 0) / vals.length;
    });

    new Chart(document.getElementById("chartDisponibilidad"), {
      type: "line",
      data: {
        labels: periodos.map(p => new Date(p).toLocaleDateString('es-MX', { month: 'short', year: '2-digit' })),
        datasets: [{
          label: "Disponibilidad",
          data: promedios,
          borderColor: COLOR_PRIMARY,
          backgroundColor: COLOR_PRIMARY,
          tension: 0.3,
          fill: false,
          pointRadius: 4,
          pointBackgroundColor: COLOR_PRIMARY,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: ctx => " " + ctx.parsed.y.toFixed(1) + "%" } },
        },
        scales: {
          y: { beginAtZero: false, ticks: { callback: v => v + "%" } },
        },
      },
    });
  }

  // ── 7. Tabla de indicadores por máquina ──
  async function cargarIndicadoresActuales() {
    const filas = await fetchData('v1/kpi/indicadores-actuales/'); // [{Codigo, Maquina, Estado, Linea, MTTR, MTBF, Disponibilidad, Periodo}, ...]
    const tableBody = document.querySelector('.kpi__table tbody');
    if (!tableBody) return;

    tableBody.innerHTML = '';
    filas.slice(0, 6).forEach(m => {
      const clase = BADGE_POR_ESTADO[(m.Estado || '').toLowerCase()] || 'kpi__badge--info';
      const dispo = m.Disponibilidad || 0;

      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${m.Codigo || ''}</td>
        <td>${m.Maquina || ''}</td>
        <td><span class="kpi__badge ${clase}">${m.Estado || '-'}</span></td>
        <td>${m.MTTR != null ? m.MTTR.toFixed(1) : '0.0'}</td>
        <td>${m.MTBF != null ? m.MTBF.toFixed(0) : '0'}</td>
        <td><div class="kpi__bar"><div class="kpi__bar-fill" style="width:${Math.min(100, Math.max(0, dispo))}%"></div></div> ${dispo.toFixed(1)}%</td>
      `;
      tableBody.appendChild(row);
    });
  }

  // ── 8. Subtítulo con el resumen (MTBF/MTTR/Disponibilidad promedio) ──
  async function cargarResumen() {
    const r = await fetchData('v1/resumen/');
    const subtitle = document.querySelector('.kpi__sub');
    if (subtitle) {
      subtitle.textContent =
        'MTBF promedio: ' + (r.mtbf_promedio ?? 'N/A') + ' h · ' +
        'MTTR promedio: ' + (r.mttr_promedio ?? 'N/A') + ' h · ' +
        'Disponibilidad: ' + (r.disponibilidad_promedio ?? 'N/A') + '%';
    }
  }

  async function loadDashboardData() {

    const tareas = [
      ['estado de la flota', cargarEstadoFlota],
      ['fallas abiertas / órdenes activas', cargarReportesAtencion],
      ['stock', cargarStock],
      ['fallas por máquina', cargarFallasPorMaquina],
      ['mantenimiento por línea', cargarMantenimientoPorLinea],
      ['disponibilidad', cargarDisponibilidad],
      ['indicadores actuales', cargarIndicadoresActuales],
      ['resumen', cargarResumen],
    ];

    for (const [nombre, fn] of tareas) {
      try {
        await fn();
      } catch (error) {
        console.error('Error cargando ' + nombre + ':', error);
      }
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadDashboardData);
  } else {
    loadDashboardData();
  }

  window.dashboard = { reload: loadDashboardData, fetchData: fetchData };
})();