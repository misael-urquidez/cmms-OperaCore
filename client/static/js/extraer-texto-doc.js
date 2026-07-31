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
              return contenido.items.map(function (it) { return it.str; }).join(" ");
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
