$(function () {

    /* ==========================================
       1. LÓGICA DE FILTRADO Y PAGINACIÓN
       ========================================== */
    var estadoSeleccionado = "";
    var paginaActual = 1;
    var elementosPorPagina = 10;

    function normalizarTexto(texto) {
        return (texto || "")
            .toString()
            .toLowerCase()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .trim();
    }

    function aplicarFiltros() {
    var textoBusqueda = normalizarTexto($("#inputBuscar").val());
    var maquinaVal = normalizarTexto($("#filterMaquina").val());
    var severidadVal = normalizarTexto($("#filterSeveridad").val());
    var fechaDesde = $("#filterDesde").val();
    var fechaHasta = $("#filterHasta").val();

    var $tarjetasCoincidentes = $();

    $(".report-card-item").each(function () {
        var $item = $(this);
        
        var cardAsunto = normalizarTexto($item.attr("data-asunto"));
        var cardMaquina = normalizarTexto($item.attr("data-maquina"));
        var cardSeveridad = normalizarTexto($item.attr("data-severidad"));
        var cardEstado = normalizarTexto($item.attr("data-estado"));
        var cardFecha = $item.attr("data-fecha");

        // 1. Filtro por Estado (Tabs)
        var cumpleEstado = !estadoSeleccionado || (cardEstado === normalizarTexto(estadoSeleccionado));

        // 2. Filtro por Máquina
        var cumpleMaquina = !maquinaVal || (cardMaquina.indexOf(maquinaVal) !== -1);

        // 3. Filtro por Severidad
        var cumpleSeveridad = !severidadVal || (cardSeveridad.indexOf(severidadVal) !== -1);

        // 4. Búsqueda por texto general (Asunto o Máquina)
        var cumpleTexto = !textoBusqueda ||
                          (cardAsunto.indexOf(textoBusqueda) !== -1) ||
                          (cardMaquina.indexOf(textoBusqueda) !== -1);

        // 5. Rango de Fechas
        var cumpleFecha = true;
        if (cardFecha) {
            var fechaCardStr = cardFecha.toString().substring(0, 10);
            if (fechaDesde && fechaCardStr < fechaDesde) cumpleFecha = false;
            if (fechaHasta && fechaCardStr > fechaHasta) cumpleFecha = false;
        }

        if (cumpleEstado && cumpleMaquina && cumpleSeveridad && cumpleTexto && cumpleFecha) {
            $tarjetasCoincidentes = $tarjetasCoincidentes.add($item);
        } else {
            $item.hide();
        }
    });

    // Paginación dinámica
    renderizarPaginacion($tarjetasCoincidentes);
}

    function renderizarPaginacion($itemsVisibles) {
        var totalItems = $itemsVisibles.length;
        var totalPaginas = Math.ceil(totalItems / elementosPorPagina) || 1;

        if (paginaActual > totalPaginas) paginaActual = 1;

        // Ocultar todas las tarjetas filtradas primero
        $(".report-card-item").hide();

        // Mostrar únicamente las 10 tarjetas de la página activa
        var inicio = (paginaActual - 1) * elementosPorPagina;
        var fin = inicio + elementosPorPagina;
        $itemsVisibles.slice(inicio, fin).css("display", "grid");

        // Construir barra del paginador
        var $paginador = $("#paginadorReportes");
        if (!$paginador.length) {
            $("#listaReportesCards").after('<div id="paginadorReportes" class="paginador-container"></div>');
            $paginador = $("#paginadorReportes");
        }
        $paginador.empty();

        if (totalPaginas <= 1) return;

        var htmlControles = '<div class="pagination-wrapper">';
        htmlControles += '<button type="button" class="pag-btn" id="pagPrev" ' + (paginaActual === 1 ? 'disabled' : '') + '>&laquo; Anterior</button>';

        for (var i = 1; i <= totalPaginas; i++) {
            var activeClass = (i === paginaActual) ? ' active' : '';
            htmlControles += '<button type="button" class="pag-btn num-btn' + activeClass + '" data-page="' + i + '">' + i + '</button>';
        }

        htmlControles += '<button type="button" class="pag-btn" id="pagNext" ' + (paginaActual === totalPaginas ? 'disabled' : '') + '>Siguiente &raquo;</button>';
        htmlControles += '</div>';

        $paginador.html(htmlControles);
    }

    // Eventos Paginador
    $(document).on("click", ".num-btn", function () {
        paginaActual = parseInt($(this).data("page"));
        aplicarFiltros();
    });

    $(document).on("click", "#pagPrev", function () {
        if (paginaActual > 1) {
            paginaActual--;
            aplicarFiltros();
        }
    });

    $(document).on("click", "#pagNext", function () {
        paginaActual++;
        aplicarFiltros();
    });

    // Eventos Filtros
    $(".tab-btn").on("click", function () {
        $(".tab-btn").removeClass("active");
        $(this).addClass("active");
        estadoSeleccionado = $(this).attr("data-tab-status") || "";
        paginaActual = 1;
        aplicarFiltros();
    });

    $("#inputBuscar").on("input keyup search", function () {
        paginaActual = 1;
        aplicarFiltros();
    });

    $("#filterMaquina, #filterSeveridad, #filterDesde, #filterHasta").on("change", function () {
        paginaActual = 1;
        aplicarFiltros();
    });

    // Ejecutar filtro al cargar la página
    aplicarFiltros();
});