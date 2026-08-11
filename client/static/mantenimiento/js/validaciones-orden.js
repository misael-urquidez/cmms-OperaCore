document.addEventListener("DOMContentLoaded", function () {
//   var estadoElement = document.getElementById("estado");
  setupInputValidation(
    document.getElementById("oDescripcion"),
    {
      required: true,
      minLength: 10,
      maxLength: 500,
      minWords: 3,
      customValidator: (value) => {
        if (value.includes("...") || value.includes("!!")) {
          return "No se permiten múltiples caracteres especiales consecutivos";
        }
        return true;
      },
    },
    document.getElementById("descripcion-error")
    // estadoElement,
  );

});
