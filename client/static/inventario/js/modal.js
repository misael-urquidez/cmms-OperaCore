(function () {
  /* ---- abrir modal de proveedor ---- */
  window.abrirModalProveedor = function (codigo) {
    var container = document.getElementById("modal-proveedor");
    container.innerHTML = "";
    fetch("/inventario/modal/proveedor/" + codigo + "/")
      .then(function (r) { return r.text(); })
      .then(function (html) {
        container.innerHTML = html;
        container.classList.add("is-open");
      })
      .catch(function () {
        container.innerHTML =
          '<div class="fallas-modal__dialog" role="document">' +
          '<div class="fallas-modal__content">' +
          '<div class="fallas-modal__header">' +
          '<h2 class="fallas-modal__title">Error</h2>' +
          '</div>' +
          '<div class="fallas-modal__body">' +
          '<p>No se pudo cargar la información del proveedor.</p>' +
          '</div>' +
          '</div></div>';
        container.classList.add("is-open");
      });
  };

  /* ---- abrir modal de existencia ---- */
  window.abrirModalExistencia = function (refaccionId) {
    var container = document.getElementById("modal-existencia");
    container.innerHTML = "";
    fetch("/inventario/modal/existencia/" + refaccionId + "/")
      .then(function (r) { return r.text(); })
      .then(function (html) {
        container.innerHTML = html;
        container.classList.add("is-open");
      })
      .catch(function () {
        container.innerHTML =
          '<div class="fallas-modal__dialog" role="document">' +
          '<div class="fallas-modal__content">' +
          '<div class="fallas-modal__header">' +
          '<h2 class="fallas-modal__title">Error</h2>' +
          '</div>' +
          '<div class="fallas-modal__body">' +
          '<p>No se pudo cargar la existencia de la refacción.</p>' +
          '</div>' +
          '</div></div>';
        container.classList.add("is-open");
      });
  };


  /* ---- cerrar modal ---- */
  function cerrarModal(container) {
    if (!container.classList.contains("is-open")) return;
    container.classList.remove("is-open");
    container.innerHTML = "";
  }

  /* click en botones data-dismiss */
  document.addEventListener("click", function (e) {
    if (e.target.matches("[data-dismiss='modal']")) {
      var modal = e.target.closest(".fallas-modal");
      if (modal) cerrarModal(modal);
    }
  });

  /* click en backdrop */
  document.addEventListener("click", function (e) {
    if (e.target.classList.contains("fallas-modal__backdrop")) {
      var modal = e.target.closest(".fallas-modal");
      if (modal) cerrarModal(modal);
    }
  });

  /* tecla Escape */
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      document.querySelectorAll(".fallas-modal.is-open").forEach(cerrarModal);
    }
  });
})();

