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
    email: false,
    url: false,
    alphanumeric: false,
    lowercase: false,
    uppercase: false,
    noSpaces: false,
    ...options,
  };

  let cleanValue = config.trim ? value.trim() : value;

  if (config.required && (!cleanValue || cleanValue.length === 0)) {
    errors.push("Este campo es obligatorio");
  }

  if (!config.required && (!cleanValue || cleanValue.length === 0)) {
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
    errors.push(`El formato no es válido`);
  }

  if (config.allowedChars) {
    const allowedSet = new Set(config.allowedChars);
    const hasInvalidChars = [...cleanValue].some(
      (char) => !allowedSet.has(char),
    );
    if (hasInvalidChars) {
      errors.push(`Solo se permiten los caracteres: ${config.allowedChars}`);
    }
  }

  if (config.notAllowedChars) {
    const notAllowedSet = new Set(config.notAllowedChars);
    const hasInvalidChars = [...cleanValue].some((char) =>
      notAllowedSet.has(char),
    );
    if (hasInvalidChars) {
      errors.push(`No se permiten los caracteres: ${config.notAllowedChars}`);
    }
  }
  if (config.email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(cleanValue)) {
      errors.push("Debe ser un email válido");
    }
  }

  if (config.url) {
    try {
      new URL(cleanValue);
    } catch {
      errors.push("Debe ser una URL válida");
    }
  }

  if (config.alphanumeric && !/^[a-zA-Z0-9]+$/.test(cleanValue)) {
    errors.push("Solo se permiten caracteres alfanuméricos");
  }

  if (config.lowercase && cleanValue !== cleanValue.toLowerCase()) {
    errors.push("Solo se permiten minúsculas");
  }

  if (config.uppercase && cleanValue !== cleanValue.toUpperCase()) {
    errors.push("Solo se permiten mayúsculas");
  }

  if (config.noSpaces && /\s/.test(cleanValue)) {
    errors.push("No se permiten espacios");
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
    const id = input.id;
    const errorSpan = document.getElementById("horas-error");
    if (errorSpan) {
      const tieneError = errorSpan.textContent.length > 0;
      const status = tieneError ? "Inválido" : "Válido";

      const label = input.placeholder || input.id;
      html += `${label}: ${status}<br>`;
      if (tieneError) todosValidos = false;
    }
  });

  html += `<br><strong>Estado general: ${
    todosValidos ? "Perfecto" : "El boton no se activara porque hay erroes"
  }</strong>`;
  estadoElement.innerHTML = html;
}

// Validaciones para el reporte de falla

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

  //   setupInputValidation(
  //     document.getElementById("descripcion"),
  //     {
  //       required: true,
  //       minLength: 10,
  //       maxLength: 500,
  //       minWords: 3,
  //       maxWords: 50,
  //       customValidator: (value) => {
  //         if (value.includes("...") || value.includes("!!")) {
  //           return "No se permiten múltiples caracteres especiales consecutivos";
  //         }
  //         return true;
  //       },
  //     },
  //     document.getElementById("descripcion-error"),
  //     estadoElement,
  //   );
});