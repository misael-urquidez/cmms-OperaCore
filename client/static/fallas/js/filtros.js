$(function () {

    /* ==========================================
       LÓGICA DE FILTRADO DINÁMICO
       ========================================== */
    var estadoSeleccionado = "";

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
        var maquinaSeleccionada = normalizarTexto($("#filterMaquina").val());
        var severidadSeleccionada = normalizarTexto($("#filterSeveridad").val());
        var fechaDesde = $("#filterDesde").val();
        var fechaHasta = $("#filterHasta").val();

        $(".report-card-item").each(function () {
            var $item = $(this);
            var cardAsunto = normalizarTexto($item.attr("data-asunto"));
            var cardMaquina = normalizarTexto($item.attr("data-maquina"));
            var cardSeveridad = normalizarTexto($item.attr("data-severidad"));
            var cardEstado = normalizarTexto($item.attr("data-estado"));
            var cardFecha = $item.attr("data-fecha");

            // 1. Filtro por Estado (Tabs)
            var cumpleEstado = !estadoSeleccionado || (cardEstado === normalizarTexto(estadoSeleccionado));

            // 2. Filtro por Máquina (Compara presencia del texto del select en data-maquina)
            var cumpleMaquina = !maquinaSeleccionada || (cardMaquina.indexOf(maquinaSeleccionada) !== -1);

            // 3. Filtro por Severidad
            var cumpleSeveridad = !severidadSeleccionada || (cardSeveridad === severidadSeleccionada);

            // 4. Búsqueda por texto general (asunto o máquina)
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

            // Aplicar visibilidad
            if (cumpleEstado && cumpleMaquina && cumpleSeveridad && cumpleTexto && cumpleFecha) {
                $item.css("display", "grid");
            } else {
                $item.hide();
            }
        });
    }

    // Eventos
    $(".tab-btn").on("click", function () {
        $(".tab-btn").removeClass("active");
        $(this).addClass("active");
        estadoSeleccionado = $(this).attr("data-tab-status") || "";
        aplicarFiltros();
    });

    $("#inputBuscar").on("input keyup search", aplicarFiltros);
    $("#filterMaquina, #filterSeveridad, #filterDesde, #filterHasta").on("change", aplicarFiltros);

    /* ==========================================
       MODALES (DETALLE Y EXPORTACIÓN)
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
        $("#export-csv-link").attr("href", "/fallas/reporte/" + pk + "/export/csv/");
        $("#export-xlsx-link").attr("href", "/fallas/reporte/" + pk + "/export/xlsx/");
        $("#export-pdf-link").attr("href", "/fallas/reporte/" + pk + "/export/pdf/");
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

});