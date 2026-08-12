document.addEventListener("DOMContentLoaded", function () {

  /* ==========================================================================
     PARTE 1: MODAL AL REGRESAR DE REDIRECCIÓN (?levantar_orden=1)
     ========================================================================== */
  const params = new URLSearchParams(window.location.search);
  if (params.get("levantar_orden") === "1") {
    const reporte = params.get("reporte");
    const asunto = params.get("asunto") || "";
    const maquina = params.get("maquina") || "";

    window.history.replaceState({}, "", window.location.pathname);

    if (reporte) {
      const modalOrdenHtml = `
        <div class="fallas-modal is-open" id="modalConfirmarOrden" style="z-index: 100000; display: flex;">
          <div class="fallas-modal__backdrop"></div>
          <div class="fallas-modal__dialog" style="max-width: 480px;">
            <div class="fallas-modal__content" style="text-align: center; padding: 1.75rem;">
              <div style="background: rgba(56, 189, 248, 0.12); color: #38bdf8; width: 56px; height: 56px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem auto;">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
              </div>
              <h3 class="fallas-modal__title" style="margin-bottom: 0.5rem; font-size: 1.2rem;">¡Reporte #${reporte} Registrado!</h3>
              <p style="color: var(--color-muted, #94a3b8); font-size: 0.875rem; margin-bottom: 1.5rem; line-height: 1.4;">
                El reporte de falla ha sido generado exitosamente. ¿Deseas levantar la <strong>Orden de Mantenimiento Correctiva</strong> ahora?
              </p>
              <div style="display: flex; gap: 0.75rem; justify-content: center;">
                <button type="button" class="fallas-modal__btn fallas-modal__btn--close" id="btnCancelarOrden" style="flex: 1;">No, más tarde</button>
                <button type="button" class="fallas-modal__btn fallas-modal__btn--primary" id="btnAceptarOrden" style="flex: 1; background: var(--color-primary, #38bdf8); color: #0f172a; font-weight: 700;">Sí, crear orden</button>
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


  /* ==========================================================================
     PARTE 2: INTERCEPTAR BOTÓN Y MOSTRAR MODAL PREVIO
     ========================================================================== */
  const form = document.querySelector("form");
  const btnAbrir = document.getElementById("btnAbrirConfirm");
  const modal = document.getElementById("modalConfirmarReporte");
  const btnCerrar = document.getElementById("btnCerrarConfirm");
  const btnCancelar = document.getElementById("btnCancelarConfirm");
  const btnGuardar = document.getElementById("btnGuardarDefinitivo");

  if (!form || !modal) return;

  // Al presionar "Reportar falla"
  if (btnAbrir) {
    btnAbrir.addEventListener("click", function () {
      // Validar si los campos requeridos del formulario HTML están llenos
      if (!form.checkValidity()) {
        form.reportValidity(); // Muestra los mensajes de error nativos del navegador si falta algo
        return;
      }

      // Copiar valores al modal de confirmación
      const selectMaquina = document.getElementById("maquina");
      const selectSeveridad = document.getElementById("tipo_severidad");

      const confAsunto = document.getElementById("confAsunto");
      const confMaquina = document.getElementById("confMaquina");
      const confSeveridad = document.getElementById("confSeveridad");
      const confCausa = document.getElementById("confCausa");
      const confTiempo = document.getElementById("confTiempo");

      if (confAsunto) confAsunto.textContent = document.getElementById("asunto")?.value || "-";
      if (confMaquina) confMaquina.textContent = selectMaquina?.options[selectMaquina.selectedIndex]?.text || "-";
      if (confSeveridad) confSeveridad.textContent = selectSeveridad?.options[selectSeveridad.selectedIndex]?.text || "-";
      if (confCausa) confCausa.textContent = document.getElementById("causaRaiz")?.value || "-";
      if (confTiempo) confTiempo.textContent = document.getElementById("tiempoParo")?.value || "0";

      // Vista previa de la imagen si se seleccionó una
      const fileInput = document.getElementById("fileDrag");
      const confImgContainer = document.getElementById("confImagenContainer");
      const confImgPreview = document.getElementById("confImagenPreview");

      if (fileInput && fileInput.files && fileInput.files[0]) {
        const reader = new FileReader();
        reader.onload = function (evt) {
          if (confImgPreview) confImgPreview.src = evt.target.result;
          if (confImgContainer) confImgContainer.style.display = "block";
        };
        reader.readAsDataURL(fileInput.files[0]);
      } else {
        if (confImgContainer) confImgContainer.style.display = "none";
      }

      // Abrir modal de confirmación
      modal.style.display = "flex";
      modal.classList.add("is-open");
    });
  }

  function cerrarModal() {
    modal.style.display = "none";
    modal.classList.remove("is-open");
  }

  if (btnCerrar) btnCerrar.addEventListener("click", cerrarModal);
  if (btnCancelar) btnCancelar.addEventListener("click", cerrarModal);

  // Al presionar "Confirmar y Guardar" dentro del modal
  if (btnGuardar) {
    btnGuardar.addEventListener("click", function () {
      btnGuardar.disabled = true;
      btnGuardar.textContent = "Guardando...";

      const formData = new FormData(form);

      fetch(form.action, {
        method: "POST",
        body: formData,
        headers: {
          "X-Requested-With": "XMLHttpRequest"
        }
      })
      .then(response => {
        if (response.redirected) {
          mostrarAvisoExito(response.url);
        } else if (response.ok) {
          const redirectUrl = form.dataset.redirectUrl || "/fallas/lista/";
          mostrarAvisoExito(redirectUrl);
        } else {
          return response.text().then(text => { throw new Error(text); });
        }
      })
      .catch(error => {
        alert("Ocurrió un error al guardar el reporte: " + error.message);
        btnGuardar.disabled = false;
        btnGuardar.textContent = "Confirmar y Guardar";
        cerrarModal();
      });
    });
  }

  function mostrarAvisoExito(redirectUrl) {
    const modalContent = modal.querySelector(".fallas-modal__content");
    if (modalContent) {
      modalContent.innerHTML = `
        <div style="text-align:center; padding: 1.5rem 0;">
          <div style="background: rgba(16, 185, 129, 0.12); color: #10b981; width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 0.75rem auto;">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
          </div>
          <h3 style="color:#10b981; margin:0 0 0.5rem 0;">¡Reporte registrado con éxito!</h3>
          <p style="color:#cbd5e1; font-size:0.85rem;">La falla ha sido guardada en estado Abierto.</p>
        </div>
      `;
    }
    setTimeout(() => {
      window.location.href = redirectUrl;
    }, 1500);
  }
});