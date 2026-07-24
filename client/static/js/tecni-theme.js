/* ==========================================================================
   Apariencia del técnico: SOLO permite elegir entre 3 temas fijos
   (Oscuro/Claro/Plano). No hay fondo, degradado ni personalización avanzada
   — a propósito, por eso este archivo es mucho más corto que theme.js.
   ========================================================================== */
(function () {
  const body = document.body;
  const userMenu = document.getElementById("userMenu");
  const username = (userMenu && userMenu.dataset.username) || "invitado";
  const KEY = `operacore_apariencia_tecni_${username}`;

  function leer() {
    try {
      const raw = JSON.parse(localStorage.getItem(KEY) || "{}");
      return { theme: raw.theme === "light" || raw.theme === "plain" ? raw.theme : "dark" };
    } catch (e) {
      return { theme: "dark" };
    }
  }
  function guardar(prefs) {
    try { localStorage.setItem(KEY, JSON.stringify(prefs)); } catch (e) {}
  }

  function aplicar(prefs) {
    if (prefs.theme === "light" || prefs.theme === "plain") body.dataset.theme = prefs.theme;
    else delete body.dataset.theme;
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
  function pintar() {
    if (!themeToggle) return;
    themeToggle.querySelectorAll("[data-theme-value]").forEach((b) => {
      b.classList.toggle("is-active", b.dataset.themeValue === prefs.theme);
    });
  }
  pintar();

  if (themeToggle) {
    themeToggle.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-theme-value]");
      if (!btn) return;
      prefs = { theme: btn.dataset.themeValue };
      guardar(prefs);
      aplicar(prefs);
      pintar();
    });
  }
})();
