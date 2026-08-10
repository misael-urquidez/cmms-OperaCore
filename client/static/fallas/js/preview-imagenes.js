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

        const archivoArrastable = document.getElementById('fileDrag');
        const previewDrag = document.getElementById('previewDrag');
        const dropZone = document.getElementById('dropZoneLabel');

        if (archivoArrastable && previewDrag && dropZone){
            // ELIMINAR ESTE BLOQUE HACE QUE SE NECESITE DOBLE CLICK:
            /*
            dropZone.addEventListener('click', function(evento){
                if(evento.target === this || evento.target.closest('.drop-zone')){
                    archivoArrastable.click();
                }
            });
            */

            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, (evento) => {
                    evento.preventDefault();
                    evento.stopPropagation();
                });
            });

            dropZone.addEventListener('dragover', ()=>{
                dropZone.style.borderColor = 'var(--color-primary)';
                dropZone.style.background = 'rgba(56, 189, 248, 0.05)';
            });

            dropZone.addEventListener('dragleave', () => {
                dropZone.style.borderColor = '';
                dropZone.style.background = '';
                });

            dropZone.addEventListener('drop', (evento) => {
                const files = evento.dataTransfer.files;

                if (files.length > 0) {
                    // Creamos un DataTransfer para asignar los archivos de forma limpia
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(files[0]); // Toma la primera imagen

                    // Limpiamos e ingresamos el archivo de forma explícita
                    archivoArrastable.files = dataTransfer.files;

                    // Disparamos manualmente el evento change
                    archivoArrastable.dispatchEvent(new Event('change', { bubbles: true }));
                }

                dropZone.style.borderColor = '#94a3b8';
                dropZone.style.background = '#fafcff';
            });

      archivoArrastable.addEventListener('change', function() {
        actualizarPreview(this, previewDrag);
        const file = this.files[0];
        const p = dropZone.querySelector('p');
        const span = dropZone.querySelector('span');
        if (file && file.type.startsWith('image/')) {
          if (p) p.textContent = `${file.name}`;
          if (span) span.textContent = `${(file.size / 1024).toFixed(1)} KB`;
        } else if (file) {
          if (p) p.textContent = `${file.name}`;
          if (span) span.textContent = `tamaño: ${(file.size / 1024).toFixed(1)} KB`;
        } else {
          if (p) p.textContent = 'Suelta tu imagen aquí';
          if (span) span.textContent = 'o haz clic para explorar';
        }
      });
    }
}
};
