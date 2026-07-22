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
            dropZone.addEventListener('click', function(evento){
                if(evento.target === this || evento.target.closest('.drop-zone')){
                    archivoArrastable.click();
                }
            });

            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, (evento) => {
                    evento.preventDefault();
                    evento.stopPropagation();
                });
            });

            dropZone.addEventListener('dragover', ()=>{
                dropZone.style.borderColor = '#2563eb';
                dropZone.style.background = '#eef2ff';
            });

            dropZone.addEventListener('dragleave', () => {
                dropZone.style.borderColor = '#94a3b8';
                dropZone.style.background = '#fafcff';
                });

                dropZone.addEventListener('drop', (evento) => {
        const dt = evento.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
          archivoArrastable.files = files;
          const event = new Event('change', { bubbles: true });
          archivoArrastable.dispatchEvent(event);
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