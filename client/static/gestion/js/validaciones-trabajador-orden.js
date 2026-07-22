document.addEventListener("DOMContentLoaded", function () {
  var estadoElement = document.getElementById("estado");

  setupInputValidation(
    document.getElementById("id_orden_mantenimiento"),
    { required: true, maxLength: 15 },
    document.getElementById("orden_mantenimiento-error"),
    estadoElement,
  );
});
