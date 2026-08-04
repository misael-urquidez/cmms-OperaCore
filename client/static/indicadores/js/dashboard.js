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

  var COLOR_TEXT = cssVar("--color-text", "#e2e8f0");
  var COLOR_MUTED = cssVar("--color-muted", "#94a3b8");
  var COLOR_GRID = "rgba(148, 163, 184, 0.15)";
  var COLOR_PRIMARY = cssVar("--color-primary", "#38bdf8");

  Chart.defaults.color = COLOR_MUTED;
  Chart.defaults.borderColor = COLOR_GRID;
  Chart.defaults.font.family = "'Segoe UI', system-ui, sans-serif";

  var PALETA_ESTADOS = ["#34d399", "#fb7185", "#fbbf24", "#94a3b8", "#64748b"];

  // 1. Estado de la flota (doughnut)
  new Chart(document.getElementById("chartFlota"), {
    type: "doughnut",
    data: {
      labels: ["Operativa", "En falla", "En mantenimiento", "En espera", "Deshabilitada"],
      datasets: [{
        data: [12, 3, 2, 1, 1],
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
        tooltip: { callbacks: { label: function (ctx) { return " " + ctx.label + ": " + ctx.parsed + " máq."; } } },
      },
    },
  });

  // 2. Top máquinas con más fallas (barras horizontales / Pareto)
  new Chart(document.getElementById("chartFallas"), {
    type: "bar",
    data: {
      labels: ["MAQ006 Est. Prueba", "MAQ003 AOI Inspector", "MAQ002 Horno Reflow", "MAQ001 Pick & Place", "MAQ004 Dispensador"],
      datasets: [{
        data: [12, 8, 6, 4, 3],
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
        tooltip: { callbacks: { label: function (ctx) { return " " + ctx.parsed.x + " fallas"; } } },
      },
      scales: {
        x: { beginAtZero: true, ticks: { precision: 0 } },
      },
    },
  });

  // 3. Mantenimiento preventivo vs correctivo por línea
  new Chart(document.getElementById("chartMantenimiento"), {
    type: "bar",
    data: {
      labels: ["Línea de Producción 1", "Línea de Producción 2"],
      datasets: [
        { label: "Preventivo", data: [14, 8], backgroundColor: COLOR_PRIMARY, borderRadius: 6 },
        { label: "Correctivo", data: [9, 7], backgroundColor: "#fb7185", borderRadius: 6 },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "top", labels: { boxWidth: 12, boxHeight: 12, padding: 12 } } },
      scales: {
        x: { stacked: false },
        y: { beginAtZero: true, ticks: { precision: 0 } },
      },
    },
  });

  // 4. Disponibilidad de la planta (línea, últimos 6 meses)
  new Chart(document.getElementById("chartDisponibilidad"), {
    type: "line",
    data: {
      labels: ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio"],
      datasets: [{
        label: "Disponibilidad",
        data: [95.2, 96.1, 94.8, 96.5, 97.2, 96.8],
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
        tooltip: { callbacks: { label: function (ctx) { return " " + ctx.parsed.y.toFixed(1) + "%"; } } },
      },
      scales: {
        y: {
          beginAtZero: false,
          min: 90,
          max: 100,
          ticks: { callback: function (v) { return v + "%"; } },
        },
      },
    },
  });
})();
