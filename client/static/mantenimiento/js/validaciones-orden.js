function reglasTextoOrden() {
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

function reglasDescripcionOrden() {
  var reglas = reglasTextoOrden();
  reglas.required = true;
  return reglas;
}

document.addEventListener("DOMContentLoaded", function () {
  var estadoNuevaOrden = document.getElementById("estadoNuevaOrden");

  setupInputValidation(
    document.getElementById("oDescripcion"),
    reglasDescripcionOrden(),
    document.getElementById("descripcion-error"),
    estadoNuevaOrden,
  );

  var estadoEditar = document.getElementById("estadoEditarOrden");

  setupInputValidation(
    document.getElementById("edDescripcion"),
    reglasDescripcionOrden(),
    document.getElementById("edDescripcion-error"),
    estadoEditar,
  );

  setupInputValidation(
    document.getElementById("edNotas"),
    reglasTextoOrden(),
    document.getElementById("edNotas-error"),
    estadoEditar,
  );

  setupInputValidation(
    document.getElementById("edDiagnostico"),
    reglasTextoOrden(),
    document.getElementById("edDiagnostico-error"),
    estadoEditar,
  );

  setupInputValidation(
    document.getElementById("edHoras"),
    {
      required: false,
      customValidator: (value) => {
        if (!value) return true;
        const num = parseFloat(value);
        if (isNaN(num)) return "Debe ser un número válido";
        if (num < 0) return "No puede ser un número negativo";
        return true;
      },
    },
    document.getElementById("edHoras-error"),
    estadoEditar,
  );

  var editarBtn = document.getElementById("ordenEditarBtn");
  if (editarBtn) {
    editarBtn.addEventListener("click", function () {
      [
        ["edDescripcion", "edDescripcion-error"],
        ["edNotas", "edNotas-error"],
        ["edDiagnostico", "edDiagnostico-error"],
        ["edHoras", "edHoras-error"],
      ].forEach(function (par) {
        var el = document.getElementById(par[0]);
        var err = document.getElementById(par[1]);
        if (el) {
          el.style.borderColor = "";
          el.style.borderWidth = "";
        }
        if (err) err.textContent = "";
      });
      actualizarEstado(estadoEditar);
    });
  }
});
