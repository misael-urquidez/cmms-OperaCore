/* ==========================================================================
   JS del panel técnico: colapsar/abrir sidebar. Copia recortada de admin.js
   con su propia key de localStorage para no interferir con el admin.
   ========================================================================== */
(function () {
  const shell = document.querySelector(".tecni-shell");
  if (!shell) return;

  document.querySelectorAll(".tecni-sidebar__group-toggle").forEach((btn) => {
    btn.addEventListener("click", () => {
      const group = btn.closest(".tecni-sidebar__group");
      const abierto = group.classList.toggle("is-open");
      btn.setAttribute("aria-expanded", abierto ? "true" : "false");
    });
  });

  const collapseBtn = document.getElementById("tecniSidebarCollapse");
  const COLLAPSE_KEY = "operacore_tecni_sidebar_collapsed";

  if (localStorage.getItem(COLLAPSE_KEY) === "1") {
    shell.classList.add("is-collapsed");
  }

  if (collapseBtn) {
    collapseBtn.addEventListener("click", () => {
      const colapsado = shell.classList.toggle("is-collapsed");
      try { localStorage.setItem(COLLAPSE_KEY, colapsado ? "1" : "0"); } catch (e) {}
    });
  }

  const openBtn = document.getElementById("tecniSidebarOpen");
  const backdrop = document.getElementById("tecniSidebarBackdrop");

  function cerrarMovil() { shell.classList.remove("is-mobile-open"); }

  if (openBtn) openBtn.addEventListener("click", () => shell.classList.add("is-mobile-open"));
  if (backdrop) backdrop.addEventListener("click", cerrarMovil);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") cerrarMovil(); });
})();
