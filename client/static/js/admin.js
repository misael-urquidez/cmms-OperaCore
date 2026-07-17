/* ==========================================================================
   JS del panel admin: grupos desplegables del sidebar, colapsar en
   escritorio y abrir/cerrar en móvil. El estado colapsado se recuerda
   en localStorage para que no "brinque" al navegar entre páginas.
   ========================================================================== */
(function () {
  const shell = document.querySelector(".admin-shell");
  if (!shell) return;

  /* ---------- grupos desplegables (submenús) ---------- */
  document.querySelectorAll(".sidebar__group-toggle").forEach((btn) => {
    btn.addEventListener("click", () => {
      const group = btn.closest(".sidebar__group");
      const abierto = group.classList.toggle("is-open");
      btn.setAttribute("aria-expanded", abierto ? "true" : "false");
    });
  });

  /* ---------- colapsar sidebar (escritorio) ---------- */
  const collapseBtn = document.getElementById("sidebarCollapse");
  const COLLAPSE_KEY = "operacore_sidebar_collapsed";

  if (localStorage.getItem(COLLAPSE_KEY) === "1") {
    shell.classList.add("is-collapsed");
  }

  if (collapseBtn) {
    collapseBtn.addEventListener("click", () => {
      const colapsado = shell.classList.toggle("is-collapsed");
      try {
        localStorage.setItem(COLLAPSE_KEY, colapsado ? "1" : "0");
      } catch (e) { /* modo privado: no pasa nada */ }
    });
  }

  /* ---------- abrir/cerrar en móvil ---------- */
  const openBtn = document.getElementById("sidebarOpen");
  const backdrop = document.getElementById("sidebarBackdrop");

  function cerrarMovil() { shell.classList.remove("is-mobile-open"); }

  if (openBtn) {
    openBtn.addEventListener("click", () => shell.classList.add("is-mobile-open"));
  }
  if (backdrop) backdrop.addEventListener("click", cerrarMovil);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") cerrarMovil();
  });
})();
