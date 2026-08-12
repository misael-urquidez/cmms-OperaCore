document.addEventListener("DOMContentLoaded", function () {
  var estadoElement = document.getElementById("estadoCerrarOrden");
  if (!estadoElement) return;

  function reglasTexto() {
    return {
      required: false,
      minLength: 10,
      maxLength: 500,
      minWords: 3,
      customValidator: (value) => {
        if (value.includes("...") || value.includes("!!")) {
          return "No se permiten múltiples caracteres especiales consecutivos";
        }
        return true;
      },
    };
  }

  setupInputValidation(
    document.getElementById("twDiagnostico"),
    reglasTexto(),
    document.getElementById("twDiagnostico-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("twNotas"),
    reglasTexto(),
    document.getElementById("twNotas-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("twHoras"),
    {
      required: true,
      customValidator: (value) => {
        const num = parseFloat(value);
        if (isNaN(num)) return "Debe ser un número válido";
        if (num < 0) return "No puede ser un número negativo";
        return true;
      },
    },
    document.getElementById("twHoras-error"),
    estadoElement,
  );
});
