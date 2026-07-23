document.addEventListener("DOMContentLoaded", function () {
  var estadoElement = document.getElementById("estado");

  setupInputValidation(
    document.getElementById("id_cantidad"),
    { required: true },
    document.getElementById("cantidad-error"),
    estadoElement,
  );
});
