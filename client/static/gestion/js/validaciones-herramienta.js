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
    document.getElementById("id_stock"),
    {
      required: true,
      customValidator: (value) => {
        const num = parseInt(value, 10);
        if (isNaN(num)) return "Debe ser un número entero";
        if (num < 0) return "No puede ser un número negativo";
        return true;
      },
    },
    document.getElementById("stock-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_imagen"),
    { required: false, pattern: /^(https?:\/\/)?[^\s]+$/ },
    document.getElementById("imagen-error"),
    estadoElement,
  );
});
