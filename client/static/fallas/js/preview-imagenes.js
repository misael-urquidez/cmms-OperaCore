document.addEventListener("DOMContentLoaded", function () {
  const fileInput = document.getElementById("fileDrag");
  const dropZone = document.getElementById("dropZoneLabel");
  const previewBox = document.getElementById("previewDrag");

  if (!fileInput || !dropZone || !previewBox) return;

  // Prevenir comportamientos por defecto del navegador al arrastrar
  ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
  });

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  // Destacar zona al arrastrar
  ["dragenter", "dragover"].forEach((eventName) => {
    dropZone.addEventListener(eventName, () => dropZone.classList.add("highlight"), false);
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(eventName, () => dropZone.classList.remove("highlight"), false);
  });

  // Manejar el Soltar archivo (Drop)
  dropZone.addEventListener("drop", function (e) {
    const dt = e.dataTransfer;
    const files = dt.files;

    if (files && files.length > 0) {
      // CLAVE AQUÍ: Asignar los archivos arrastrados directamente al input file
      fileInput.files = files;
      mostrarVistaPrevia(files[0]);
    }
  });

  // Manejar la selección normal por clic (Click)
  fileInput.addEventListener("change", function () {
    if (this.files && this.files[0]) {
      mostrarVistaPrevia(this.files[0]);
    }
  });

  // Función para renderizar la imagen en el contenedor
  function mostrarVistaPrevia(file) {
    if (!file.type.startsWith("image/")) {
      alert("Por favor selecciona un archivo de imagen válido.");
      return;
    }

    const reader = new FileReader();
    reader.onload = function (e) {
      previewBox.innerHTML = `<img src="${e.target.result}" alt="Vista previa de evidencia" style="max-width:100%; max-height: 200px; border-radius:6px; object-fit: cover;">`;
    };
    reader.readAsDataURL(file);
  }
});