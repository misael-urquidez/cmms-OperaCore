document.querySelector('details').removeAttribute('open');


(function (){

    function actualizarPreview(inputElement, previewContainer, infoElement = null, clearButton = null){
        const archivo = inputElement.files[0];

        previewContainer.innerHTML = '';

        if (archivo && archivo.type.startsWith('image/')){
            const reader = new FileReader();

            reader.onload = function(evento){
                const imagen = document.createElement('img');
                imagen.src = evento.target.result;
                imagen.alt = archivo.name;
                previewContainer.appendChild(imagen);

                if(infoElement){
                    infoElement.textContent = archivo.name;
                }

                if(clearButton){
                    clearButton.disabled = false;
                }

            };

            reader.readAsDataURL(archivo);
        } else {
            const placeholder = document.createElement('span');
            placeholder.className = 'placeholder';
            placeholder.textContent = archivo ? 'Archivo no compatible' : 'Vista previa';
            previewContainer.appendChild(placeholder);
            if(infoElement){
                infoElement.textContent = archivo ? archivo.name : 'ninguna';
            }
            if (clearButton) {
                clearButton.disabled = true;
            }
        }
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


        
        
        

    
})();