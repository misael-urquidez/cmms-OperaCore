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
            
            // Usamos .attr() directo de la tarjeta para evitar problemas de cache de jQuery
            var cardAsunto = normalizarTexto($item.attr("data-asunto"));
            var cardMaquina = normalizarTexto($item.attr("data-maquina"));
            var cardSeveridad = normalizarTexto($item.attr("data-severidad"));
            var cardEstado = normalizarTexto($item.attr("data-estado"));
            var cardFecha = $item.attr("data-fecha");

            // 1. Filtro por Estado (Tabs)
            var cumpleEstado = !estadoSeleccionado || (cardEstado === normalizarTexto(estadoSeleccionado));

            // 2. Filtro por Máquina (Búsqueda tokenizada por palabras)
            var cumpleMaquina = true;
            if (maquinaVal !== "") {
                var tokensMaquina = maquinaVal.split(/\s+/);
                cumpleMaquina = tokensMaquina.some(function (token) {
                    return token.length > 0 && cardMaquina.indexOf(token) !== -1;
                });
            }

            // 3. Filtro por Severidad
            var cumpleSeveridad = true;
            if (severidadVal !== "") {
                cumpleSeveridad = cardSeveridad.indexOf(severidadVal) !== -1 || severidadVal.indexOf(cardSeveridad) !== -1;
            }

            // 4. Búsqueda por texto general
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

    /* ==========================================
       2. MODALES (DETALLE Y EXPORTACIÓN)
       ========================================== */
    function abrir_modal_detalle(pk) {
        var $modal = $("#detalle-falla");
        $modal.empty();

        $.get("/fallas/detalle/reporte/" + pk + "/")
            .done(function (html) {
                $modal.html(html);
                $modal.addClass("is-open");
            })
            .fail(function () {
                $modal.html(
                    '<div class="fallas-modal__dialog" role="document">' +
                    '<div class="fallas-modal__content">' +
                    '<div class="fallas-modal__header">' +
                    '<h2 class="fallas-modal__title">Error</h2>' +
                    '<button class="fallas-modal__close" data-dismiss="modal">&times;</button>' +
                    '</div>' +
                    '<div class="fallas-modal__body">' +
                    '<p>No se pudo cargar el detalle del reporte.</p>' +
                    '</div>' +
                    '</div></div>'
                );
                $modal.addClass("is-open");
            });
    }

    function abrir_modal_exportar(pk) {
        $("#export-pk").text(pk);

        var urlCsv  = (window.URL_EXPORTAR_CSV  || "/fallas/exportar/csv/0/").replace("0", pk);
        var urlXlsx = (window.URL_EXPORTAR_XLSX || "/fallas/exportar/xlsx/0/").replace("0", pk);
        var urlPdf  = (window.URL_EXPORTAR_PDF  || "/fallas/exportar/pdf/0/").replace("0", pk);

        $("#export-csv-link").attr("href", urlCsv);
        $("#export-xlsx-link").attr("href", urlXlsx);
        $("#export-pdf-link").attr("href", urlPdf);

        $("#exportar-falla").addClass("is-open");
    }

    function cerrar_modales() {
        $(".fallas-modal").removeClass("is-open");
        $("#detalle-falla").empty();
        document.dispatchEvent(new CustomEvent("fallas:modal-cerrado"));
    }

    $(document).on("click", "[data-dismiss='modal'], [data-dismiss='modal-export']", cerrar_modales);
    $(document).on("click", ".fallas-modal__backdrop", cerrar_modales);
    $(document).on("keydown", function (e) {
        if (e.key === "Escape") cerrar_modales();
    });

    window.abrir_modal_detalle = abrir_modal_detalle;
    window.abrir_modal_exportar = abrir_modal_exportar;

    // Ejecutar filtro al cargar la página
    aplicarFiltros();
});