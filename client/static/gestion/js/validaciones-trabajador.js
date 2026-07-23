document.addEventListener("DOMContentLoaded", function () {
  var estadoElement = document.getElementById("estado");
  var isEdicion = window.location.pathname.indexOf("/editar/") !== -1;

  setupInputValidation(
    document.getElementById("id_numeroNomina"),
    {
      required: true,
      maxLength: 15,
      pattern: /^EMP\d{4}$/,
      customValidator: function (value) {
        if (!/^EMP\d{4}$/.test(value)) {
          return "Formato: EMP seguido de 4 dígitos (ej. EMP0001)";
        }
        return true;
      },
    },
    document.getElementById("numeroNomina-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_nombre"),
    {
      required: true,
      maxLength: 50,
      pattern: /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/,
    },
    document.getElementById("nombre-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_apellidoPat"),
    {
      required: true,
      maxLength: 50,
      pattern: /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/,
    },
    document.getElementById("apellidoPat-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_apellidoMat"),
    {
      required: false,
      maxLength: 50,
      pattern: /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/,
    },
    document.getElementById("apellidoMat-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_telefono"),
    {
      required: true,
      maxLength: 15,
      pattern: /^\d+$/,
      customValidator: function (value) {
        if (!/^\d+$/.test(value)) {
          return "Solo se permiten números";
        }
        return true;
      },
    },
    document.getElementById("telefono-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_correo"),
    {
      required: true,
      maxLength: 100,
      email: true,
    },
    document.getElementById("correo-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("id_usuario"),
    {
      required: true,
      maxLength: 30,
      noSpaces: true,
      pattern: /^[a-zA-Z0-9_]+$/,
      customValidator: function (value) {
        if (/\s/.test(value)) {
          return "No se permiten espacios";
        }
        if (!/^[a-zA-Z0-9_]+$/.test(value)) {
          return "Solo letras, números y guión bajo";
        }
        return true;
      },
    },
    document.getElementById("usuario-error"),
    estadoElement,
  );

  if (!isEdicion) {
    setupInputValidation(
      document.getElementById("id_password"),
      {
        required: true,
        minLength: 8,
        customValidator: function (value) {
          if (value.length < 8) return "Mínimo 8 caracteres";
          return true;
        },
      },
      document.getElementById("password-error"),
      estadoElement,
    );

    setupInputValidation(
      document.getElementById("id_password2"),
      {
        required: true,
        customValidator: function (value) {
          var password = document.getElementById("id_password");
          if (password && value !== password.value) {
            return "Las contraseñas no coinciden";
          }
          return true;
        },
      },
      document.getElementById("password2-error"),
      estadoElement,
    );
  }
});
