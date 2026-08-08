/* ==========================================================================
   Apariencia del técnico: 3 temas fijos + color personalizado para el logo.
   El color del logo se guarda por usuario y se aplica como CSS variable.
   ========================================================================== */
(function () {
  const body = document.body;
  const userMenu = document.getElementById("userMenu");
  const username = (userMenu && userMenu.dataset.username) || "invitado";
  const KEY = `operacore_apariencia_tecni_${username}`;

  function leer() {
    try {
      const raw = JSON.parse(localStorage.getItem(KEY) || "{}");
      return {
        theme: raw.theme === "light" || raw.theme === "plain" ? raw.theme : "dark",
        logoColor: raw.logoColor || "#38bdf8"  // azul por defecto
      };
    } catch (e) {
      return { theme: "dark", logoColor: "#38bdf8" };
    }
  }

  function guardar(prefs) {
    try { localStorage.setItem(KEY, JSON.stringify(prefs)); } catch (e) {}
  }

  function aplicar(prefs) {
    // Tema
    if (prefs.theme === "light" || prefs.theme === "plain") body.dataset.theme = prefs.theme;
    else delete body.dataset.theme;

    // Color del logo
    document.documentElement.style.setProperty("--brand-color", prefs.logoColor);
  }

  let prefs = leer();
  aplicar(prefs);

  /* pestañas del modal (Cuenta / Apariencia) */
  const tabBtns = document.querySelectorAll("[data-cfg-tab]");
  const tabPanels = document.querySelectorAll("[data-cfg-panel]");
  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabBtns.forEach((b) => b.classList.toggle("is-active", b === btn));
      tabPanels.forEach((p) => p.classList.toggle("is-active", p.dataset.cfgPanel === btn.dataset.cfgTab));
    });
  });

  /* selector de tema */
  const themeToggle = document.getElementById("themeToggle");
  function pintarTema() {
    if (!themeToggle) return;
    themeToggle.querySelectorAll("[data-theme-value]").forEach((b) => {
      b.classList.toggle("is-active", b.dataset.themeValue === prefs.theme);
    });
  }
  pintarTema();

  if (themeToggle) {
    themeToggle.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-theme-value]");
      if (!btn) return;
      prefs.theme = btn.dataset.themeValue;
      guardar(prefs);
      aplicar(prefs);
      pintarTema();
    });
  }

  /* selector de color del logo */
  const logoSwatches = document.getElementById("logoColorSwatches");
  const logoColorInput = document.getElementById("logoColorInput");

  function pintarColor() {
    if (!logoSwatches || !logoColorInput) return;
    logoSwatches.querySelectorAll("button").forEach((b) => {
      b.classList.toggle("is-active", b.dataset.color === prefs.logoColor);
    });
    logoColorInput.value = prefs.logoColor;
  }
  pintarColor();

  if (logoSwatches) {
    logoSwatches.addEventListener("click", (e) => {
      const btn = e.target.closest("button[data-color]");
      if (!btn) return;
      prefs.logoColor = btn.dataset.color;
      guardar(prefs);
      aplicar(prefs);
      pintarColor();
    });
  }

  if (logoColorInput) {
    logoColorInput.addEventListener("input", (e) => {
      prefs.logoColor = e.target.value;
      guardar(prefs);
      aplicar(prefs);
      pintarColor();
    });
  }
})();