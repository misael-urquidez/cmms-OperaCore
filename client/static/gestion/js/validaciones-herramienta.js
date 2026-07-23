document.addEventListener("DOMContentLoaded", function () {
  var estadoElement = document.getElementById("estado");

  setupInputValidation(
    document.getElementById("id_nombre"),
    { required: true, maxLength: 100 },
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
    document.getElementById("id_imagen"),
    { required: false, pattern: /^(https?:\/\/)?[^\s]+$/ },
    document.getElementById("imagen-error"),
    estadoElement,
  );
});
