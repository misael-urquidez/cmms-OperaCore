/* ==========================================================================
   JS del panel técnico: Gestión del Sidebar (Escritorio y Móvil).
   Independiente del admin.js para evitar conflictos de estado (localStorage).
   ========================================================================== */
(function () {
    "use strict";

    // 1. Referencias al DOM (Mejora de rendimiento)
    const DOM = {
        shell: document.querySelector(".tecni-shell"),
        groupToggles: document.querySelectorAll(".tecni-sidebar__group-toggle"),
        collapseBtn: document.getElementById("tecniSidebarCollapse"),
        openBtn: document.getElementById("tecniSidebarOpen"),
        backdrop: document.getElementById("tecniSidebarBackdrop"),
    };

    // Si no estamos en la vista del técnico, abortar la ejecución
    if (!DOM.shell) return;

    const COLLAPSE_KEY = "operacore_tecni_sidebar_collapsed";

    // ==========================================
    // Lógica de Submenús (Acordeón)
    // ==========================================
    function initGroups() {
        DOM.groupToggles.forEach((btn) => {
            btn.addEventListener("click", () => {
                const group = btn.closest(".tecni-sidebar__group");
                if (!group) return;
                
                const isNowOpen = group.classList.toggle("is-open");
                btn.setAttribute("aria-expanded", isNowOpen.toString());
            });
        });
    }

    // ==========================================
    // Lógica de Colapso (Escritorio)
    // ==========================================
    function initDesktopCollapse() {
        // Cargar estado inicial desde almacenamiento local
        try {
            if (localStorage.getItem(COLLAPSE_KEY) === "1") {
                DOM.shell.classList.add("is-collapsed");
            }
        } catch (e) {
            console.warn("OperaCore: No se pudo acceder a localStorage para el sidebar.", e);
        }

        // Evento de botón para colapsar/expandir
        if (DOM.collapseBtn) {
            DOM.collapseBtn.addEventListener("click", () => {
                const isCollapsed = DOM.shell.classList.toggle("is-collapsed");
                
                // Accesibilidad: Actualizar el estado del botón
                DOM.collapseBtn.setAttribute("aria-expanded", (!isCollapsed).toString());
                
                try {
                    localStorage.setItem(COLLAPSE_KEY, isCollapsed ? "1" : "0");
                } catch (e) {
                    console.warn("OperaCore: No se pudo guardar el estado del sidebar.");
                }
            });
        }
    }

    // ==========================================
    // Lógica de Menú Móvil
    // ==========================================
    function initMobileMenu() {
        const closeMobileMenu = () => {
            DOM.shell.classList.remove("is-mobile-open");
            if (DOM.backdrop) DOM.backdrop.setAttribute("aria-hidden", "true");
        };

        const openMobileMenu = () => {
            DOM.shell.classList.add("is-mobile-open");
            if (DOM.backdrop) DOM.backdrop.setAttribute("aria-hidden", "false");
        };

        if (DOM.openBtn) {
            DOM.openBtn.addEventListener("click", openMobileMenu);
        }

        if (DOM.backdrop) {
            DOM.backdrop.addEventListener("click", closeMobileMenu);
        }

        // Permitir cerrar el menú móvil con la tecla Escape
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape" && DOM.shell.classList.contains("is-mobile-open")) {
                closeMobileMenu();
            }
        });
    }

    // Inicializar todos los módulos
    initGroups();
    initDesktopCollapse();
    initMobileMenu();

})();