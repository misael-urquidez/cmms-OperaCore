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
                    '</div>' +
                    '<div class="fallas-modal__body">' +
                    '<p>No se pudo cargar el detalle del reporte.</p>' +
                    '</div>' +
                    '</div></div>'
                );
                $modal.addClass("is-open");
            });
    }

    /* ---- cerrar modal ---- */

    function cerrar_modal() {
        var $modal = $("#detalle-falla");
        // Escape se escucha siempre, tambien con el modal cerrado: sin este
        // guard avisariamos "se cerro" sin que hubiera nada abierto, y quien
        // escucha restauraria su contexto sin venir al caso.
        if (!$modal.hasClass("is-open")) return;
        $modal.removeClass("is-open").empty();
        // Quien nos abrio (p.ej. el drawer de mantenimiento, que se cierra
        // para no taparnos) puede escuchar esto y restaurar su contexto.
        document.dispatchEvent(new CustomEvent("fallas:modal-cerrado"));
    }

    $(document).on("click", "[data-dismiss='modal']", cerrar_modal);
    $(document).on("click", ".fallas-modal__backdrop", cerrar_modal);
    $(document).on("keydown", function (e) {
        if (e.key === "Escape") cerrar_modal();
    });

    /* ---- exponer al global ---- */

    window.abrir_modal_detalle = abrir_modal_detalle;

});
