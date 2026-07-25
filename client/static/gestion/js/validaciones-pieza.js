document.addEventListener("DOMContentLoaded", function () {
  var estadoElement = document.getElementById("estado");

  setupInputValidation(
    document.getElementById("id_numeroserie"),
    { required: true, maxLength: 50 },
    document.getElementById("numeroserie-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_codigoetiqueta"),
    { required: false, maxLength: 50 },
    document.getElementById("codigoetiqueta-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_nombre"),
    { required: true, maxLength: 100 },
    document.getElementById("nombre-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_costoinicial"),
    { required: true },
    document.getElementById("costoinicial-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_horasoperacion"),
    { required: false },
    document.getElementById("horasoperacion-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_tiempovidautil"),
    { required: true },
    document.getElementById("tiempovidautil-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_depresacionanual"),
    { required: false },
    document.getElementById("depresacionanual-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_valorresidual"),
    { required: false },
    document.getElementById("valorresidual-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_fechainstalacion"),
    { required: true },
    document.getElementById("fechainstalacion-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_fechagarantia"),
    { required: false },
    document.getElementById("fechagarantia-error"),
    estadoElement,
  );
});
