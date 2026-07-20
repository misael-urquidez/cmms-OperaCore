$(function () {

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

    function cerrar_modal() {
        $("#detalle-falla").removeClass("is-open").empty();
    }

    // delegacion: funciona para contenido cargado via AJAX
    $(document).on("click", "[data-dismiss='modal']", cerrar_modal);
    $(document).on("click", ".fallas-modal__backdrop", cerrar_modal);

    // tecla Escape cierra el modal
    $(document).on("keydown", function (e) {
        if (e.key === "Escape") cerrar_modal();
    });

    // exponer al scope global para el onclick del boton
    window.abrir_modal_detalle = abrir_modal_detalle;

});
