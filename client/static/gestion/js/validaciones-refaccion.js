document.addEventListener("DOMContentLoaded", function () {
  var estadoElement = document.getElementById("estado");

  setupInputValidation(
    document.getElementById("id_nombre"),
    { required: true, maxLength: 100 },
    document.getElementById("nombre-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_codigosku"),
    { required: true, maxLength: 50 },
    document.getElementById("codigosku-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_puntoreorden"),
    { required: false },
    document.getElementById("puntoreorden-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_codigoinventario"),
    { required: true, maxLength: 50 },
    document.getElementById("codigoinventario-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_numeroorden"),
    { required: true, maxLength: 15 },
    document.getElementById("numeroorden-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_costo"),
    { required: true },
    document.getElementById("costo-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_tiempoentregaapr"),
    { required: false },
    document.getElementById("tiempoentregaapr-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_stock"),
    { required: true },
    document.getElementById("stock-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_stockminimo"),
    { required: true },
    document.getElementById("stockminimo-error"),
    estadoElement,
  );
});
