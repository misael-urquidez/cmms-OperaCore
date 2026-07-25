document.addEventListener("DOMContentLoaded", function () {
  var estadoElement = document.getElementById("estado");

  setupInputValidation(
    document.getElementById("id_reporte_falla"),
    { required: true },
    document.getElementById("reporte_falla-error"),
    estadoElement,
  );
});
