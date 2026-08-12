document.addEventListener("DOMContentLoaded", function () {
  // Leer los parámetros enviados por el redireccionamiento de Django
  const params = new URLSearchParams(window.location.search);
  
  if (params.get("levantar_orden") === "1") {
    const reporte = params.get("reporte");
    const asunto = params.get("asunto") || "";
    const maquina = params.get("maquina") || "";

    // Limpia la URL para evitar que el modal vuelva a salir si se recarga la página
    window.history.replaceState({}, "", window.location.pathname);

    if (reporte) {
      const modalOrdenHtml = `
        <div class="fallas-modal is-open" id="modalConfirmarOrden" style="display: flex; z-index: 100000;">
          <div class="fallas-modal__backdrop"></div>
          <div class="fallas-modal__dialog" style="max-width: 480px;">
            <div class="fallas-modal__content" style="text-align: center; padding: 1.75rem;">
              
              <div style="background: rgba(56, 189, 248, 0.12); color: #38bdf8; width: 56px; height: 56px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem auto;">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
              </div>

              <h3 class="fallas-modal__title" style="margin-bottom: 0.5rem; font-size: 1.2rem; color: #f8fafc;">¡Reporte #${reporte} Registrado!</h3>
              <p style="color: var(--color-muted, #94a3b8); font-size: 0.875rem; margin-bottom: 1.5rem; line-height: 1.4;">
                El reporte de falla ha sido generado exitosamente. ¿Deseas levantar la <strong>Orden de Mantenimiento Correctiva</strong> ahora?
              </p>

              <div style="display: flex; gap: 0.75rem; justify-content: center;">
                <button type="button" class="fallas-modal__btn fallas-modal__btn--close" id="btnCancelarOrden" style="flex: 1;">
                  No, más tarde
                </button>
                <button type="button" class="fallas-modal__btn fallas-modal__btn--primary" id="btnAceptarOrden" style="flex: 1; background: var(--color-primary, #38bdf8); color: #0f172a; font-weight: 700;">
                  Sí, crear orden
                </button>
              </div>

            </div>
          </div>
        </div>
      `;

      document.body.insertAdjacentHTML("beforeend", modalOrdenHtml);

      document.getElementById("btnCancelarOrden")?.addEventListener("click", function () {
        document.getElementById("modalConfirmarOrden")?.remove();
      });

      document.getElementById("btnAceptarOrden")?.addEventListener("click", function () {
        const urlTarget = "/mantenimiento/?maquina=" + encodeURIComponent(maquina) +
                          "&tipo=CORRE&reporte=" + encodeURIComponent(reporte) +
                          "&asunto=" + encodeURIComponent(asunto);
        window.location.href = urlTarget;
      });
    }
  }
});