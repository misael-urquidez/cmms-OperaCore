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

    /* ---- abrir modal de actualizar (formulario) ---- */

    function abrir_modal_actualizar(pk) {
        var $modal = $("#detalle-falla");
        $modal.empty();

        $.get("/fallas/actualizar/reporte/" + pk + "/")
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
                    '<p>No se pudo cargar el formulario de actualización.</p>' +
                    '</div>' +
                    '</div></div>'
                );
                $modal.addClass("is-open");
            });
    }

    /* ---- enviar actualización (PATCH al API) ---- */

    $(document).on("submit", "#form-actualizar-reporte", function (e) {
        e.preventDefault();

        var $form = $(this);
        var pk = $form.data("pk");
        var apiBase = $form.data("api");
        var formData = new FormData(this);

        $.ajax({
            url: apiBase + "/fallas/v2/reportes/update/" + pk + "/",
            method: "PATCH",
            data: formData,
            processData: false,
            contentType: false,
            success: function () {
                cerrar_modal();
                $.post("/fallas/invalidar-cache/reportes/").always(function () {
                    location.reload();
                });
            },
            error: function () {
                alert("Error al guardar los cambios.");
            }
        });
    });

    /* ---- cerrar modal ---- */

    function cerrar_modal() {
        $("#detalle-falla").removeClass("is-open").empty();
    }

    $(document).on("click", "[data-dismiss='modal']", cerrar_modal);
    $(document).on("click", ".fallas-modal__backdrop", cerrar_modal);
    $(document).on("keydown", function (e) {
        if (e.key === "Escape") cerrar_modal();
    });

    /* ---- exponer al global ---- */

    window.abrir_modal_detalle = abrir_modal_detalle;
    window.abrir_modal_actualizar = abrir_modal_actualizar;

});
