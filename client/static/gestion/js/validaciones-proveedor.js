document.addEventListener("DOMContentLoaded", function () {
  var estadoElement = document.getElementById("estado");

  setupInputValidation(
    document.getElementById("id_codigo"),
    { required: true, maxLength: 15 },
    document.getElementById("codigo-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_rfc"),
    { required: true, maxLength: 13, alphanumeric: true },
    document.getElementById("rfc-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_razonsocial"),
    { required: true, maxLength: 100 },
    document.getElementById("razonsocial-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_nombrecomercial"),
    { required: true, maxLength: 100 },
    document.getElementById("nombrecomercial-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_telefono"),
    { required: true, pattern: /^[0-9]+$/, maxLength: 20 },
    document.getElementById("telefono-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_email"),
    { required: true, pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, maxLength: 100 },
    document.getElementById("email-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_dircalle"),
    { required: true, maxLength: 100 },
    document.getElementById("dircalle-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_dircodigopostal"),
    { required: true, pattern: /^[0-9]{5}$/, maxLength: 5 },
    document.getElementById("dircodigopostal-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_dirnumero"),
    { required: true, maxLength: 10 },
    document.getElementById("dirnumero-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_contnombre"),
    { required: true, maxLength: 50, pattern: /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/ },
    document.getElementById("contnombre-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_contapellpat"),
    { required: true, maxLength: 50, pattern: /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/ },
    document.getElementById("contapellpat-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_contapellmat"),
    { required: false, maxLength: 50, pattern: /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]*$/ },
    document.getElementById("contapellmat-error"),
    estadoElement,
  );
});
