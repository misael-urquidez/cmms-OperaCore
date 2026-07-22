var contador = 0;

function sincronizarFallas() {
    var base = document.getElementById("tipo_falla");
    var dynamic = document.querySelectorAll("#nuevas-fallas select");
    var allSelects = [base].concat(Array.from(dynamic));

    var selectedBySelect = allSelects.map(function(sel) {
        return sel.value;
    });

    allSelects.forEach(function(sel, idx) {
        var opciones = sel.options;
        for (var i = 0; i < opciones.length; i++) {
            if (opciones[i].value === "") continue;
            var usadoEnOtro = selectedBySelect.some(function(v, j) {
                return j !== idx && v === opciones[i].value;
            });
            opciones[i].disabled = usadoEnOtro;
        }
    });
}

function anadirFalla() {
    contador++;
    var contenedor = document.getElementById("nuevas-fallas");
    var selectOriginal = document.getElementById("tipo_falla");

    var nuevoDiv = document.createElement("div");
    nuevoDiv.className = "falla-dynamic";
    nuevoDiv.setAttribute("data-index", contador);

    var nuevoSelect = document.createElement("select");
    nuevoSelect.className = "falla-select";
    nuevoSelect.name = "tipo_falla_" + contador;
    nuevoSelect.required = true;

    var placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "Seleccione...";
    nuevoSelect.appendChild(placeholder);

    var opciones = selectOriginal.options;
    for (var i = 1; i < opciones.length; i++) {
        var opt = document.createElement("option");
        opt.value = opciones[i].value;
        opt.textContent = opciones[i].textContent;
        nuevoSelect.appendChild(opt);
    }

    nuevoSelect.addEventListener("change", sincronizarFallas);

    nuevoDiv.appendChild(nuevoSelect);
    contenedor.appendChild(nuevoDiv);
    sincronizarFallas();
}

function quitarSelect(tipo) {
    var contenedor, selector;
    if (tipo === "tipo-falla") {
        contenedor = document.getElementById("nuevas-fallas");
        selector = ".falla-dynamic";
    }
    if (contenedor) {
        var items = contenedor.querySelectorAll(selector);
        if (items.length > 0) {
            contenedor.removeChild(items[items.length - 1]);
            sincronizarFallas();
        }
    }
}

document.addEventListener("DOMContentLoaded", function() {
    var base = document.getElementById("tipo_falla");
    if (base) {
        base.addEventListener("change", sincronizarFallas);
        sincronizarFallas();
    }
});
