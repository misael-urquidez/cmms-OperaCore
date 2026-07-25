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
    document.getElementById("id_imagen_url"),
    { required: false, maxLength: 255, customValidator: function(v){
      if (!v) return true;
      try { new URL(v); return true; } catch(e) { return "Debe ser una URL válida"; }
    } },
    document.getElementById("imagen_url-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_fechainstalacion"),
    { required: true },
    document.getElementById("fechainstalacion-error"),
    estadoElement,
  );
});
