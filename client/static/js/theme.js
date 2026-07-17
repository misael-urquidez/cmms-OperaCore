/* ==========================================================================
   Personalización de apariencia. Prototipo: se guarda en localStorage por
   usuario. Aplica en todas las páginas que carguen este script; los
   controles viven en la pestaña "Apariencia" del modal de configuración.

   Temas:
   - dark  (original) / light: personalizables (fondo, degradado y, con el
     switch de "Personalización avanzada", acento/sidebar/textos).
   - plain: modo PROFESIONAL tipo el "Plano" del login — colores sobrios
     fijos; se bloquea la personalización de colores para mantener el look.
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
  function ajustar(hex, factor) {
    // factor <1 oscurece, >1 aclara
    const n = parseInt(hex.slice(1), 16);
    const r = clamp(Math.round(((n >> 16) & 255) * factor));
    const g = clamp(Math.round(((n >> 8) & 255) * factor));
    const b = clamp(Math.round((n & 255) * factor));
    return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, "0")}`;
  }
  function esClaro(hex) {
    const n = parseInt(hex.slice(1), 16);
    const r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
    return (0.299 * r + 0.587 * g + 0.114 * b) > 150;
  }

  /* ---------- aplicar preferencias ---------- */
  function aplicar(prefs) {
    const esPlano = prefs.theme === "plain";

    // tema base
    if (prefs.theme === "light" || prefs.theme === "plain") body.dataset.theme = prefs.theme;
    else delete body.dataset.theme;

    // limpiar todo lo inline antes de re-aplicar
    ["--color-bg", "--color-surface", "--color-primary", "--color-text",
     "--sidebar-bg1", "--sidebar-bg2", "--sidebar-text", "--topbar-bg"]
      .forEach((v) => body.style.removeProperty(v));
    body.style.removeProperty("background");
    body.style.removeProperty("background-attachment");

    if (esPlano) return; // plano = look fijo profesional, nada custom encima

    // ---- fondo de página (tambien tiñe superficie/menús para que combine) ----
    if (prefs.bgColor) {
      const c = prefs.bgColor;
      if (prefs.bgGradient) {
        body.style.background = `linear-gradient(160deg, ${ajustar(c, 1.45)} 0%, ${c} 45%, ${ajustar(c, 0.55)} 100%)`;
        body.style.backgroundAttachment = "fixed";
      } else {
        body.style.setProperty("--color-bg", c);
      }
      // superficie (tarjetas, dropdown del menú de usuario, modal) un paso
      // más clara que el fondo; sidebar/topbar a juego
      const superficie = ajustar(c, esClaro(c) ? 1.12 : 1.55);
      body.style.setProperty("--color-surface", superficie);
      body.style.setProperty("--sidebar-bg1", ajustar(c, 1.3));
      body.style.setProperty("--sidebar-bg2", ajustar(c, 0.85));
      body.style.setProperty("--topbar-bg", superficie);
    } else if (prefs.bgGradient) {
      // degradado con el fondo default del tema
      const base = prefs.theme === "light" ? "#eef2f7" : "#0f172a";
      body.style.background = `linear-gradient(160deg, ${ajustar(base, 1.35)} 0%, ${base} 45%, ${ajustar(base, 0.6)} 100%)`;
      body.style.backgroundAttachment = "fixed";
    }

    // ---- colores finos (solo con avanzado activado) ----
    if (!prefs.advanced) return;

    if (prefs.accent) body.style.setProperty("--color-primary", prefs.accent);
    if (prefs.sidebarBg) {
      body.style.setProperty("--sidebar-bg1", prefs.sidebarBg);
      body.style.setProperty("--sidebar-bg2", ajustar(prefs.sidebarBg, 0.75));
    }
    if (prefs.sidebarText) body.style.setProperty("--sidebar-text", prefs.sidebarText);
    if (prefs.textColor) body.style.setProperty("--color-text", prefs.textColor);
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
        : "Los cambios se aplican al instante y se recuerdan en este navegador.";
    }
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
