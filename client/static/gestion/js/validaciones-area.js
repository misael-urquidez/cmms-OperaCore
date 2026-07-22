document.addEventListener("DOMContentLoaded", function () {
  var estadoElement = document.getElementById("estado");

  setupInputValidation(
    document.getElementById("id_codigo"),
    { required: true, maxLength: 10, alphanumeric: true },
    document.getElementById("codigo-error"),
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
    document.getElementById("id_telefono"),
    { required: true, maxLength: 15, customValidator: function(v){ return /^\d+$/.test(v) ? true : "Solo se permiten números"; } },
    document.getElementById("telefono-error"),
    estadoElement,
  );
});
