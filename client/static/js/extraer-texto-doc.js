/* Extrae texto plano de un .docx o .pdf en el navegador, sin backend.
   Requiere mammoth.js (docx) y pdf.js (pdf) cargados antes que este script. */
window.extraerTextoDocumento = function (archivo) {
  var nombre = (archivo.name || "").toLowerCase();

  if (nombre.endsWith(".pdf")) {
    return archivo.arrayBuffer().then(function (buf) {
      return window.pdfjsLib.getDocument({ data: buf }).promise.then(function (pdf) {
        var promesas = [];
        for (var i = 1; i <= pdf.numPages; i++) {
          promesas.push(
            pdf.getPage(i).then(function (pagina) {
              return pagina.getTextContent();
            }).then(function (contenido) {
              // Reconstruye saltos de linea usando la posicion Y de cada
              // fragmento: pdf.js no los da directos, solo texto suelto.
              // Sin esto, todo el texto de la pagina queda en una sola
              // linea y el reconocimiento de plantilla (que busca cada
              // etiqueta en su propio renglon) nunca encuentra nada.
              var lineas = [];
              var lineaActual = "";
              var yAnterior = null;
              contenido.items.forEach(function (it) {
                var y = it.transform ? it.transform[5] : null;
                if (yAnterior !== null && y !== null && Math.abs(y - yAnterior) > 2) {
                  lineas.push(lineaActual);
                  lineaActual = "";
                }
                lineaActual += it.str;
                yAnterior = y;
              });
              if (lineaActual) lineas.push(lineaActual);
              return lineas.join("\n");
            })
          );
        }
        return Promise.all(promesas).then(function (paginas) { return paginas.join("\n\n"); });
      });
    });
  }

  return archivo.arrayBuffer()
    .then(function (buf) { return window.mammoth.extractRawText({ arrayBuffer: buf }); })
    .then(function (res) { return res.value || ""; });
};
