document.addEventListener("DOMContentLoaded", function () {
    var estadoElement = document.getElementById("estado");

    var campos = [
        { id: "codigo", options: { required: true, maxLength: 10, pattern: /^[a-zA-Z0-9#_\-]+$/ } },
        { id: "numeroserie", options: { required: true, maxLength: 30, pattern: /^[a-zA-Z0-9#_\-]+$/ } },
        { id: "nombre", options: { required: true, minLength: 3, maxLength: 100, pattern: /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s#_\-]+$/ } },
        { id: "descripcion", options: { maxLength: 255, minWords: 3 } },
    ];

    campos.forEach(function (campo) {
        var input = document.getElementById("id_" + campo.id);
        if (!input) return;
        input.dataset.errorId = campo.id + "-error";
        setupInputValidation(
            input,
            campo.options,
            document.getElementById(campo.id + "-error"),
            estadoElement,
        );
    });

    var requiredIds = ["numeroserie", "linea", "marca", "modelo", "estado_maquina", "tipo_maquina"];
    requiredIds.forEach(function (id) {
        var el = document.getElementById("id_" + id);
        if (el) el.required = true;
    });
});
