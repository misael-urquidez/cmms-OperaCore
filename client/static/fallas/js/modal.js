$(function () {

    /* ---- abrir modal de detalle (solo lectura) ---- */
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

    /* ---- abrir modal de exportación ---- */
    function abrir_modal_exportar(pk) {
        $("#export-pk").text(pk);
        $("#export-csv-link").attr("href", "/fallas/reporte/" + pk + "/export/csv/");
        $("#export-xlsx-link").attr("href", "/fallas/reporte/" + pk + "/export/xlsx/");
        $("#export-pdf-link").attr("href", "/fallas/reporte/" + pk + "/export/pdf/");
        $("#exportar-falla").addClass("is-open");
    }

    /* ---- cerrar modales ---- */
    function cerrar_modales() {
        $(".fallas-modal").removeClass("is-open");
        $("#detalle-falla").empty();
        document.dispatchEvent(new CustomEvent("fallas:modal-cerrado"));
    }

    // Delegación de eventos para cerrar modales (tanto el de detalle como exportar)
    $(document).on("click", "[data-dismiss='modal'], [data-dismiss='modal-export']", cerrar_modales);
    $(document).on("click", ".fallas-modal__backdrop", cerrar_modales);
    $(document).on("keydown", function (e) {
        if (e.key === "Escape") cerrar_modales();
    });

    /* ---- exponer funciones al scope global ---- */
    window.abrir_modal_detalle = abrir_modal_detalle;
    window.abrir_modal_exportar = abrir_modal_exportar;

});