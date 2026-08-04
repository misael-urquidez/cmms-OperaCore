document.addEventListener("DOMContentLoaded", function () {
  var estadoElement = document.getElementById("estado");

  setupInputValidation(
    document.getElementById("id_codigo"),
    { required: true, maxLength: 10, pattern: /^[a-zA-Z0-9#_\-]+$/ },
    document.getElementById("codigo-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_numeroserie"),
    { required: true, maxLength: 30, pattern: /^[a-zA-Z0-9#_\-]+$/ },
    document.getElementById("numeroserie-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_nombre"),
    { required: true, maxLength: 100, pattern: /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s#_\-]+$/ },
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

  ["id_numeroserie", "id_linea", "id_marca", "id_modelo", "id_estado_maquina", "id_tipo_maquina"].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.required = true;
  });
});
