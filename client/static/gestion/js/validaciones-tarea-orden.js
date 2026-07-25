document.addEventListener("DOMContentLoaded", function () {
  var estadoElement = document.getElementById("estado");

  setupInputValidation(
    document.getElementById("id_orden_mantenimiento"),
    { required: true, maxLength: 15 },
    document.getElementById("orden_mantenimiento-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_fechainicio"),
    { required: true },
    document.getElementById("fechainicio-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_fechacierre"),
    { required: false },
    document.getElementById("fechacierre-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_horainicio"),
    { required: true },
    document.getElementById("horainicio-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_horafin"),
    { required: false },
    document.getElementById("horafin-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_verificacion"),
    { required: false, customValidator: function(v){
      if (!v) return true;
      var n = parseInt(v, 10);
      if (isNaN(n) || (n !== 0 && n !== 1)) return "Debe ser 1 (sí) o 0 (no)";
      return true;
    } },
    document.getElementById("verificacion-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_observaciones"),
    { required: false, maxLength: 250 },
    document.getElementById("observaciones-error"),
    estadoElement,
  );
});
