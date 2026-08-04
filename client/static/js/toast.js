(function () {
  "use strict";

  if (window.mostrarToast) return;

  var CONTENEDOR_ID = "toastGlobalContainer";

  function contenedor() {
    var el = document.getElementById(CONTENEDOR_ID);
    if (!el) {
      el = document.createElement("ul");
      el.id = CONTENEDOR_ID;
      el.className = "messages";
      document.body.appendChild(el);
    }
    return el;
  }

  window.mostrarToast = function (mensaje, tipo) {
    var tipoValido = ["success", "warning", "error", "info"].indexOf(tipo) !== -1 ? tipo : "info";
    var item = document.createElement("li");
    item.className = "messages__item messages__item--" + tipoValido;
    item.textContent = mensaje;
    contenedor().appendChild(item);

    setTimeout(function () {
      item.classList.add("messages__item--hide");
      item.addEventListener("transitionend", function () { item.remove(); });
      setTimeout(function () { item.remove(); }, 500);
    }, 3500);
  };
})();
