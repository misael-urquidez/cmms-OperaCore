document.addEventListener("DOMContentLoaded", function () {
  const form = document.querySelector("form");
  const modal = document.getElementById("modalConfirmarReporte");
  const btnCerrar = document.getElementById("btnCerrarConfirm");
  const btnCancelar = document.getElementById("btnCancelarConfirm");
  const btnGuardar = document.getElementById("btnGuardarDefinitivo");

  if (!form || !modal) return;

  // Interceptamos el evento submit del formulario
  form.addEventListener("submit", function (e) {
    e.preventDefault();

    // Extraer textos de los elementos seleccionados
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

    // Vista previa de la evidencia en el modal de confirmación
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

    // Mostrar modal de confirmación
    modal.style.display = "flex";
  });

  function cerrarModal() {
    modal.style.display = "none";
  }

  if (btnCerrar) btnCerrar.addEventListener("click", cerrarModal);
  if (btnCancelar) btnCancelar.addEventListener("click", cerrarModal);

  // Procesar envío AJAX mediante fetch al presionar "Confirmar y Guardar"
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
          // Obtener la URL de redirección desde la respuesta o la lista por defecto
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

  // Animación / aviso de éxito antes de redirigir
  function mostrarAvisoExito(redirectUrl) {
    const modalContent = modal.querySelector(".fallas-modal__content");
    if (modalContent) {
      modalContent.innerHTML = `
        <div style="text-align:center; padding: 1.5rem 0;">
          <div style="font-size: 3rem; margin-bottom: 0.5rem;">✅</div>
          <h3 style="color:#10b981; margin:0 0 0.5rem 0;">¡Reporte registrado con éxito!</h3>
          <p style="color:#cbd5e1; font-size:0.85rem;">La falla ha sido guardada en estado Abierto y la máquina pasó a FALLO.</p>
        </div>
      `;
    }
    setTimeout(() => {
      window.location.href = redirectUrl;
    }, 1800);
  }
});