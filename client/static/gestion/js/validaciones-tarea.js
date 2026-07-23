document.addEventListener("DOMContentLoaded", function () {
  var estadoElement = document.getElementById("estado");

  setupInputValidation(
    document.getElementById("id_instruccion"),
    { required: true, maxLength: 100 },
    document.getElementById("instruccion-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_actividad"),
    { required: true, customValidator: function(v){
      var n = parseInt(v, 10);
      if (isNaN(n) || (n !== 0 && n !== 1)) return "Debe ser 1 (sí) o 0 (no)";
      return true;
    } },
    document.getElementById("actividad-error"),
    estadoElement,
  );
});
