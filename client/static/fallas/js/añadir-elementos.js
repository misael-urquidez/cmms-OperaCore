var contador = 0;

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

    nuevoDiv.appendChild(nuevoSelect);
    contenedor.appendChild(nuevoDiv);
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
        }
    }
}
