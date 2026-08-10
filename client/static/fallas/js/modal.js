$(function () {

    /* ---- abrir modal de detalle (solo lectura) ---- */
    function abrir_modal_detalle(pk) {
        var $modal = $("#detalle-falla");
        $modal.empty();

        $.get("/fallas/detalle/reporte/" + pk + "/")
            .done(function (html) {
                $modal.html(html);
                $modal.css("display", "flex").addClass("is-open");
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
                $modal.css("display", "flex").addClass("is-open");
            });
    }

    /* ---- abrir modal de exportación ---- */
    function abrir_modal_exportar(pk) {
    // Asignar el ID al texto del modal
    const exportPk = document.getElementById("export-pk");
    if (exportPk) exportPk.textContent = pk;

    // Construir las URLs remplazando el placeholder (0) con el ID real
    if (window.URL_EXPORTAR_CSV) {
        document.getElementById("export-csv-link").href = window.URL_EXPORTAR_CSV.replace('/0/', `/${pk}/`);
    }
    if (window.URL_EXPORTAR_XLSX) {
        document.getElementById("export-xlsx-link").href = window.URL_EXPORTAR_XLSX.replace('/0/', `/${pk}/`);
    }
    if (window.URL_EXPORTAR_PDF) {
        document.getElementById("export-pdf-link").href = window.URL_EXPORTAR_PDF.replace('/0/', `/${pk}/`);
    }

    // Mostrar el modal agregando la clase activa (según la convención que uses en tu CSS)
    const modalExport = document.getElementById("exportar-falla");
    if (modalExport) {
        modalExport.classList.add("is-open"); // O la clase que use tu CSS (ej: 'show', 'active')
    }
    }

    /* ---- cerrar modales ---- */
    function cerrar_modales() {
        $(".fallas-modal").removeClass("is-open").css("display", "none");
        $("#detalle-falla").empty();
        document.dispatchEvent(new CustomEvent("fallas:modal-cerrado"));
    }

    // Delegación de eventos para cerrar modales
    $(document).on("click", "[data-dismiss='modal'], [data-dismiss='modal-export']", cerrar_modales);
    $(document).on("click", ".fallas-modal__backdrop", cerrar_modales);
    $(document).on("keydown", function (e) {
        if (e.key === "Escape") cerrar_modales();
    });

    /* ---- exponer funciones al scope global ---- */
    window.abrir_modal_detalle = abrir_modal_detalle;
    window.abrir_modal_exportar = abrir_modal_exportar;

});