document.addEventListener("DOMContentLoaded", function () {
  var estadoElement = document.getElementById("estado");
  if (!estadoElement) return;

  setupInputValidation(
    document.getElementById("fCodigo"),
    { required: true, maxLength: 10, pattern: /^[a-zA-Z0-9#_\-]+$/ },
    document.getElementById("codigo-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("fNombre"),
    { required: true, minLength: 3, maxLength: 100, pattern: /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s#_\-]+$/ },
    document.getElementById("nombre-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("fSerie"),
    { required: true, maxLength: 30, pattern: /^[a-zA-Z0-9#_\-]+$/ },
    document.getElementById("serie-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("fDescripcion"),
    { required: false, maxLength: 255, minWords: 3 },
    document.getElementById("descripcion-error"),
    estadoElement,
  );

  ["fEstado", "fLinea", "fMarca", "fModelo", "fTipo", "fSerie"].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.required = true;
  });
});
