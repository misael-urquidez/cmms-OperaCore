/* ==========================================================================
   Personalización de apariencia. Prototipo: se guarda en localStorage por
   usuario. Aplica en todas las páginas que carguen este script; los
   controles viven en la pestaña "Apariencia" del modal de configuración.

   Temas:
   - dark  (original) / light: personalizables (fondo, degradado y, con el
     switch de "Personalización avanzada", acento/sidebar/textos).
   - plain: modo PROFESIONAL tipo el "Plano" del login — colores sobrios
     fijos; se bloquea la personalización de colores para mantener el look.

   NUEVO: auto-contraste. Cada vez que cambia el fondo, el degradado o el
   acento, se calcula la luminancia (WCAG) y se elige automáticamente el
   color de texto/muted/sidebar-text más legible, para evitar combinaciones
   como "texto claro sobre fondo claro". Si el usuario fija un color a mano
   en "Personalización avanzada" que igual queda con bajo contraste, no se
   le pisa su elección: se le muestra una advertencia en el modal.
   ========================================================================== */
(function () {
  const body = document.body;
  const userMenu = document.getElementById("userMenu");
  const username = (userMenu && userMenu.dataset.username) || "invitado";
  const KEY = `operacore_apariencia_${username}`;

  const DEFAULTS = {
    theme: "dark",        // dark | light | plain
    bgColor: "",          // "" = fondo por defecto del tema
    bgGradient: false,    // fondo con degradado sutil
    advanced: false,      // habilita los colores finos
    accent: "",
    sidebarBg: "",
    sidebarText: "",
    textColor: "",
  };

  /* ---------- persistencia ---------- */
  function leer() {
    try {
      return Object.assign({}, DEFAULTS, JSON.parse(localStorage.getItem(KEY) || "{}"));
    } catch (e) {
      return Object.assign({}, DEFAULTS);
    }
  }
  function guardar(prefs) {
    try { localStorage.setItem(KEY, JSON.stringify(prefs)); } catch (e) {}
  }

  /* ---------- utilidades de color ---------- */
  function clamp(v) { return Math.max(0, Math.min(255, v)); }

  function hexToRgb(hex) {
    let h = (hex || "#000000").replace("#", "");
    if (h.length === 3) h = h.split("").map((c) => c + c).join("");
    const n = parseInt(h.padEnd(6, "0").slice(0, 6), 16);
    return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 };
  }
  function rgbToHex(r, g, b) {
    return `#${[r, g, b].map((v) => clamp(Math.round(v)).toString(16).padStart(2, "0")).join("")}`;
  }

  function ajustar(hex, factor) {
    // factor <1 oscurece, >1 aclara
    const { r, g, b } = hexToRgb(hex);
    return rgbToHex(clamp(r * factor), clamp(g * factor), clamp(b * factor));
  }
  function mezclar(hexA, hexB, t) {
    // t=0 -> hexA puro, t=1 -> hexB puro
    const a = hexToRgb(hexA), b = hexToRgb(hexB);
    return rgbToHex(
      a.r + (b.r - a.r) * t,
      a.g + (b.g - a.g) * t,
      a.b + (b.b - a.b) * t
    );
  }
  function esClaro(hex) {
    const { r, g, b } = hexToRgb(hex);
    return (0.299 * r + 0.587 * g + 0.114 * b) > 150;
  }

  /* ---------- contraste WCAG ---------- */
  function luminancia(hex) {
    const { r, g, b } = hexToRgb(hex);
    const chan = (c) => {
      c /= 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    };
    return 0.2126 * chan(r) + 0.7152 * chan(g) + 0.0722 * chan(b);
  }
  function contraste(hexA, hexB) {
    const l1 = luminancia(hexA), l2 = luminancia(hexB);
    const [claro, oscuro] = l1 > l2 ? [l1, l2] : [l2, l1];
    return (claro + 0.05) / (oscuro + 0.05);
  }
  // Elige, entre un candidato oscuro y uno claro, el que mejor contraste
  // da contra el fondo indicado (así el texto siempre se lee).
  function textoLegible(fondoHex, candidatoOscuro, candidatoClaro) {
    const co = candidatoOscuro || "#0f172a";
    const cl = candidatoClaro || "#f1f5f9";
    return contraste(fondoHex, cl) >= contraste(fondoHex, co) ? cl : co;
  }
  function contrasteOK(fg, bg, minimo) {
    return contraste(fg, bg) >= minimo;
  }

  function defaultsTema(theme) {
    return theme === "light"
      ? { bg: "#eef2f7", surface: "#ffffff" }
      : { bg: "#0f172a", surface: "#1e293b" };
  }

  /* ---------- aplicar preferencias ---------- */
  function aplicar(prefs) {
    const esPlano = prefs.theme === "plain";

    // tema base
    if (prefs.theme === "light" || prefs.theme === "plain") body.dataset.theme = prefs.theme;
    else delete body.dataset.theme;

    // limpiar todo lo inline antes de re-aplicar
    ["--color-bg", "--color-surface", "--color-primary", "--color-primary-contrast",
     "--color-text", "--color-muted", "--sidebar-bg1", "--sidebar-bg2",
     "--sidebar-text", "--topbar-bg"]
      .forEach((v) => body.style.removeProperty(v));
    body.style.removeProperty("background");
    body.style.removeProperty("background-attachment");

    if (esPlano) return; // plano = look fijo profesional, nada custom encima

    const def = defaultsTema(prefs.theme);
    const fondoBase = prefs.bgColor || def.bg;

    // ---- fondo de página (también tiñe superficie/menús para que combine) ----
    let superficie = def.surface;
    let sidebarBg1, sidebarBg2, topbarBg;

    if (prefs.bgColor) {
      const c = prefs.bgColor;
      superficie = ajustar(c, esClaro(c) ? 1.12 : 1.55);
      sidebarBg1 = ajustar(c, 1.3);
      sidebarBg2 = ajustar(c, 0.85);
      topbarBg = superficie;
      body.style.setProperty("--color-bg", c);
    }

    if (prefs.bgGradient) {
      body.style.background = `linear-gradient(160deg, ${ajustar(fondoBase, 1.45)} 0%, ${fondoBase} 45%, ${ajustar(fondoBase, 0.55)} 100%)`;
      body.style.backgroundAttachment = "fixed";
    }

    if (superficie !== def.surface || prefs.bgColor) body.style.setProperty("--color-surface", superficie);
    if (sidebarBg1) body.style.setProperty("--sidebar-bg1", sidebarBg1);
    if (sidebarBg2) body.style.setProperty("--sidebar-bg2", sidebarBg2);
    if (topbarBg) body.style.setProperty("--topbar-bg", topbarBg);

    // ---- AUTO-CONTRASTE: si el fondo o el degradado cambiaron, recalcular
    // el texto para que siempre sea legible sobre el nuevo fondo/superficie ----
    if (prefs.bgColor || prefs.bgGradient) {
      const textoAuto = textoLegible(fondoBase);
      const mutedAuto = mezclar(textoAuto, fondoBase, 0.4);
      body.style.setProperty("--color-text", textoAuto);
      body.style.setProperty("--color-muted", mutedAuto);

      if (sidebarBg1 && sidebarBg2) {
        const sidebarProm = mezclar(sidebarBg1, sidebarBg2, 0.5);
        body.style.setProperty("--sidebar-text", textoLegible(sidebarProm));
      }
    }

    // ---- acento: siempre calculamos qué texto se lee mejor encima de él,
    // (botones, avatar, toggle activo) aunque el usuario no lo haya tocado ----
    const accentEfectivo = (prefs.advanced && prefs.accent) || "#38bdf8";
    body.style.setProperty("--color-primary-contrast", textoLegible(accentEfectivo, "#08131f", "#f8fafc"));

    // ---- colores finos (solo con avanzado activado) ----
    if (!prefs.advanced) return;

    if (prefs.accent) body.style.setProperty("--color-primary", prefs.accent);

    if (prefs.sidebarBg) {
      body.style.setProperty("--sidebar-bg1", prefs.sidebarBg);
      body.style.setProperty("--sidebar-bg2", ajustar(prefs.sidebarBg, 0.75));
      // si el usuario no fijó también el texto de sidebar a mano, lo
      // recalculamos para que combine con el fondo que sí eligió
      if (!prefs.sidebarText) {
        body.style.setProperty("--sidebar-text", textoLegible(prefs.sidebarBg));
      }
    }
    if (prefs.sidebarText) body.style.setProperty("--sidebar-text", prefs.sidebarText);
    if (prefs.textColor) {
      body.style.setProperty("--color-text", prefs.textColor);
      body.style.setProperty("--color-muted", mezclar(prefs.textColor, fondoBase, 0.4));
    }
  }

  let prefs = leer();
  aplicar(prefs);

  /* ---------- pestañas del modal (Cuenta / Apariencia) ---------- */
  const tabBtns = document.querySelectorAll("[data-cfg-tab]");
  const tabPanels = document.querySelectorAll("[data-cfg-panel]");

  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabBtns.forEach((b) => b.classList.toggle("is-active", b === btn));
      tabPanels.forEach((p) =>
        p.classList.toggle("is-active", p.dataset.cfgPanel === btn.dataset.cfgTab)
      );
    });
  });

  /* ---------- controles del modal (si existen en esta página) ---------- */
  const themeToggle = document.getElementById("themeToggle");
  const bgRow = document.getElementById("bgColorRow");
  const bgSwatches = document.getElementById("bgSwatches");
  const bgCustom = document.getElementById("bgCustom");
  const bgGradientRow = document.getElementById("bgGradientRow");
  const bgGradientSwitch = document.getElementById("bgGradientSwitch");
  const advancedSwitch = document.getElementById("advancedSwitch");
  const advancedBlock = document.getElementById("advancedBlock");
  const swatches = document.getElementById("accentSwatches");
  const accentCustom = document.getElementById("accentCustom");
  const sidebarBgInput = document.getElementById("sidebarBgInput");
  const sidebarTextInput = document.getElementById("sidebarTextInput");
  const textColorInput = document.getElementById("textColorInput");
  const resetBtn = document.getElementById("appearanceReset");
  const note = document.getElementById("appearanceNote");
  const warningEl = document.getElementById("appearanceWarning");

  /* ---------- DETECCIÓN de inconsistencias visuales ----------
     Esto es distinto al auto-contraste de arriba: aquí solo avisamos
     cuando el propio usuario, a mano, fijó un color de texto/acento/
     sidebar que no se lee bien — no se lo pisamos, se le informa. */
  function chequearInconsistencias() {
    if (!warningEl) return;
    const problemas = [];
    const def = defaultsTema(prefs.theme);
    const fondoBase = prefs.bgColor || def.bg;

    if (prefs.advanced && prefs.textColor && !contrasteOK(prefs.textColor, fondoBase, 4.5)) {
      problemas.push("El color de texto elegido casi no se distingue del fondo.");
    }
    if (prefs.advanced && prefs.accent) {
      const superficie = prefs.bgColor ? ajustar(prefs.bgColor, esClaro(prefs.bgColor) ? 1.12 : 1.55) : def.surface;
      if (!contrasteOK(prefs.accent, superficie, 1.6)) {
        problemas.push("El color de acento se pierde contra el fondo de las tarjetas.");
      }
    }
    if (prefs.advanced && prefs.sidebarBg && prefs.sidebarText &&
        !contrasteOK(prefs.sidebarText, prefs.sidebarBg, 4.5)) {
      problemas.push("El texto de la barra lateral no contrasta con su fondo.");
    }

    if (problemas.length) {
      warningEl.textContent = "⚠ " + problemas.join(" ");
      warningEl.classList.add("is-visible");
    } else {
      warningEl.textContent = "";
      warningEl.classList.remove("is-visible");
    }
  }

  function pintarControles() {
    const esPlano = prefs.theme === "plain";

    if (themeToggle) {
      themeToggle.querySelectorAll("[data-theme-value]").forEach((b) => {
        b.classList.toggle("is-active", b.dataset.themeValue === prefs.theme);
      });
    }

    // en plano se apagan todas las filas de personalización
    if (bgRow) bgRow.classList.toggle("is-disabled", esPlano);
    if (bgGradientRow) bgGradientRow.classList.toggle("is-disabled", esPlano);
    const advRow = advancedSwitch && advancedSwitch.closest(".config-appearance__row");
    if (advRow) advRow.classList.toggle("is-disabled", esPlano);

    if (bgSwatches) {
      bgSwatches.querySelectorAll("[data-bg-color]").forEach((b) => {
        b.classList.toggle("is-active", b.dataset.bgColor === prefs.bgColor);
      });
    }
    if (bgCustom && prefs.bgColor) bgCustom.value = prefs.bgColor;
    if (bgGradientSwitch) bgGradientSwitch.checked = prefs.bgGradient;

    if (advancedSwitch) advancedSwitch.checked = prefs.advanced;
    if (advancedBlock) advancedBlock.classList.toggle("is-open", prefs.advanced && !esPlano);

    if (swatches) {
      swatches.querySelectorAll("[data-accent]").forEach((b) => {
        b.classList.toggle("is-active", b.dataset.accent === (prefs.accent || "#38bdf8"));
      });
    }
    if (accentCustom) accentCustom.value = prefs.accent || "#38bdf8";
    if (sidebarBgInput) sidebarBgInput.value = prefs.sidebarBg || "#131c31";
    if (sidebarTextInput) sidebarTextInput.value = prefs.sidebarText || "#94a3b8";
    if (textColorInput) textColorInput.value = prefs.textColor || (prefs.theme === "light" ? "#0f172a" : "#e2e8f0");

    if (note) {
      note.textContent = esPlano
        ? "Modo plano: look profesional con colores fijos. Cambia a Oscuro o Claro para personalizar."
        : "Los cambios se aplican al instante y se recuerdan en este navegador. El contraste de texto se ajusta solo.";
    }

    chequearInconsistencias();
  }
  pintarControles();

  function actualizar(cambios) {
    prefs = Object.assign({}, prefs, cambios);
    guardar(prefs);
    aplicar(prefs);
    pintarControles();
  }

  if (themeToggle) {
    themeToggle.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-theme-value]");
      if (!btn) return;
      // al cambiar de tema se limpian fondo y color de texto manual para
      // evitar combinaciones ilegibles (texto claro sobre fondo claro, etc.)
      actualizar({ theme: btn.dataset.themeValue, bgColor: "", textColor: "" });
    });
  }

  if (bgSwatches) {
    bgSwatches.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-bg-color]");
      if (!btn) return;
      actualizar({ bgColor: btn.dataset.bgColor });
    });
  }
  if (bgCustom) bgCustom.addEventListener("input", () => actualizar({ bgColor: bgCustom.value }));
  if (bgGradientSwitch) bgGradientSwitch.addEventListener("change", () => actualizar({ bgGradient: bgGradientSwitch.checked }));

  if (advancedSwitch) {
    advancedSwitch.addEventListener("change", () => {
      if (advancedSwitch.checked) {
        actualizar({ advanced: true });
      } else {
        // al deshabilitar, se limpian los colores finos para volver al tema base
        actualizar({ advanced: false, accent: "", sidebarBg: "", sidebarText: "", textColor: "" });
      }
    });
  }

  if (swatches) {
    swatches.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-accent]");
      if (!btn) return;
      actualizar({ accent: btn.dataset.accent });
    });
  }

  if (accentCustom) accentCustom.addEventListener("input", () => actualizar({ accent: accentCustom.value }));
  if (sidebarBgInput) sidebarBgInput.addEventListener("input", () => actualizar({ sidebarBg: sidebarBgInput.value }));
  if (sidebarTextInput) sidebarTextInput.addEventListener("input", () => actualizar({ sidebarText: sidebarTextInput.value }));
  if (textColorInput) textColorInput.addEventListener("input", () => actualizar({ textColor: textColorInput.value }));

  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      prefs = Object.assign({}, DEFAULTS);
      guardar(prefs);
      aplicar(prefs);
      pintarControles();
    });
  }
})();