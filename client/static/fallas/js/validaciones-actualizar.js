function validarInputTexto(value, options = {}) {
  const errors = [];

  const config = {
    required: false,
    minLength: null,
    maxLength: null,
    pattern: null,
    customValidator: null,
    trim: true,
    allowedChars: null,
    notAllowedChars: null,
    minWords: null,
    maxWords: null,
    ...options,
  };

  let cleanValue = config.trim ? value.trim() : value;

  if (config.required && (!cleanValue || cleanValue.length === 0)) {
    errors.push("Este campo es obligatorio");
  }

  if (!cleanValue || cleanValue.length === 0) {
    return { isValid: true, errors: [], value: cleanValue };
  }

  if (config.minLength && cleanValue.length < config.minLength) {
    errors.push(`Debe tener al menos ${config.minLength} caracteres`);
  }

  if (config.maxLength && cleanValue.length > config.maxLength) {
    errors.push(`No puede tener más de ${config.maxLength} caracteres`);
  }

  if (config.minWords) {
    const wordCount = cleanValue
      .split(/\s+/)
      .filter((word) => word.length > 0).length;
    if (wordCount < config.minWords) {
      errors.push(`Debe tener al menos ${config.minWords} palabras`);
    }
  }

  if (config.maxWords) {
    const wordCount = cleanValue
      .split(/\s+/)
      .filter((word) => word.length > 0).length;
    if (wordCount > config.maxWords) {
      errors.push(`No puede tener más de ${config.maxWords} palabras`);
    }
  }

  if (config.pattern && !config.pattern.test(cleanValue)) {
    errors.push("El formato no es válido");
  }

  if (config.customValidator && typeof config.customValidator === "function") {
    const customResult = config.customValidator(cleanValue);
    if (customResult !== true) {
      errors.push(customResult || "Validación personalizada fallida");
    }
  }

  return { isValid: errors.length === 0, errors: errors, value: cleanValue };
}

function setupInputValidation(
  inputElement,
  validationOptions,
  errorElement,
  estadoElement = null,
) {
  if (!inputElement) return;

  function validarYMostrarError(mostrarError) {
    const result = validarInputTexto(inputElement.value, validationOptions);

    if (errorElement) {
      if (!result.isValid && mostrarError) {
        errorElement.textContent = "Error: " + result.errors.join(" | ");
        errorElement.style.color = "red";
        inputElement.style.borderColor = "red";
        inputElement.style.borderWidth = "2px";
      } else {
        errorElement.textContent = "";
        inputElement.style.borderColor = "";
        inputElement.style.borderWidth = "";
      }
    }

    if (estadoElement) {
      actualizarEstado(estadoElement);
    }

    return result;
  }

  inputElement.addEventListener("input", function () {
    this.dataset.touched = "true";
    validarYMostrarError(true);
  });

  inputElement.addEventListener("blur", function () {
    this.dataset.touched = "true";
    validarYMostrarError(true);
  });

  validarYMostrarError(false);
}

function actualizarEstado(estadoElement) {
  const inputs = document.querySelectorAll(
    'input[type="text"], textarea, input[type="number"]',
  );
  let todosValidos = true;
  let html = "";

  inputs.forEach((input) => {
    const errorId = input.dataset.errorId;
    if (!errorId) return;

    const errorSpan = document.getElementById(errorId);
    if (errorSpan) {
      const tieneError = errorSpan.textContent.length > 0;
      if (tieneError) todosValidos = false;
    }
  });

  html += `${
    todosValidos ? "" : "El boton no se activara porque hay errores"
  }`;
  estadoElement.innerHTML = html;

  const boton = document.getElementById("boton-registrar");
  if (boton) {
    if (!todosValidos) {
      boton.disabled = true;
      boton.style.backgroundColor = "rgba(51, 51, 51, 0.9)";
      boton.style.cursor = "not-allowed";
    } else {
      boton.disabled = false;
      boton.style.backgroundColor = "";
      boton.style.cursor = "";
    }
  }
}

document.addEventListener("DOMContentLoaded", function () {
  const estadoElement = document.getElementById("estado");

  setupInputValidation(
    document.getElementById("asunto"),
    {
      required: true,
      minLength: 2,
      maxLength: 50,
      pattern: /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/,
    },
    document.getElementById("asunto-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("descripcion"),
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
    document.getElementById("descripcion-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("causaRaiz"),
    {
      required: true,
      minLength: 10,
      maxLength: 500,
      minWords: 3,
    },
    document.getElementById("causaRaiz-error"),
    estadoElement,
  );

  setupInputValidation(
    document.getElementById("tiempoParo"),
    {
      required: true,
      customValidator: (value) => {
        const num = parseFloat(value);
        if (isNaN(num)) return "Debe ser un número válido";
        if (num < 0) return "No puede ser un número negativo";
        return true;
      },
    },
    document.getElementById("horas-error"),
    estadoElement,
  );
});
