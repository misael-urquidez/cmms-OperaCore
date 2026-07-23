document.addEventListener("DOMContentLoaded", function () {
  var estadoElement = document.getElementById("estado");

  setupInputValidation(
    document.getElementById("id_codigo"),
    { required: true, maxLength: 10, alphanumeric: true },
    document.getElementById("codigo-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_numeroserie"),
    { required: false, maxLength: 30 },
    document.getElementById("numeroserie-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_nombre"),
    { required: true, maxLength: 100, pattern: /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/ },
    document.getElementById("nombre-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_descripcion"),
    { required: false, maxLength: 255 },
    document.getElementById("descripcion-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_fechainstalacion"),
    { required: true, customValidator: function(v) {
      if (!v) return true;
      return new Date(v) <= new Date(new Date().toDateString()) ? true : "La fecha no puede ser mayor a la actual";
    }},
    document.getElementById("fechainstalacion-error"),
    estadoElement,
  );
});
