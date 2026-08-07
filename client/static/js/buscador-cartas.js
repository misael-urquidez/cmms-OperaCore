document.addEventListener("DOMContentLoaded", function () {
  var container = document.querySelector("[data-buscador-cartas]");
  if (!container) return;

  var input = container.querySelector(".buscador-cartas-input");
  var fechaInput = container.querySelector(".buscador-cartas-fecha");
  var tipoSelect = container.querySelector("#filtroTipo");
  var maquinaSelect = container.querySelector("#filtroMaquina");
  var lista = document.getElementById("ordenesList");
  if (!lista) return;

  function aplicarFiltros() {
    var texto = input ? input.value.toLowerCase() : "";
    var fechaVal = fechaInput ? fechaInput.value : "";
    var tipoVal = tipoSelect ? tipoSelect.value : "";
    var maquinaVal = maquinaSelect ? maquinaSelect.value : "";

    var cards = lista.querySelectorAll(".orden-card");
    for (var i = 0; i < cards.length; i++) {
      var card = cards[i];
      var pass = true;

      if (texto) {
        pass = card.textContent.toLowerCase().indexOf(texto) !== -1;
      }

      if (pass && fechaVal) {
        var cardFecha = card.getAttribute("data-fechaprogramada");
        pass = !!cardFecha && cardFecha <= fechaVal;
      }

      if (pass && tipoVal) {
        pass = card.getAttribute("data-tipo") === tipoVal;
      }

      if (pass && maquinaVal) {
        pass = card.getAttribute("data-maquina") === maquinaVal;
      }

      card.style.display = pass ? "" : "none";
    }
  }

  if (input) input.addEventListener("input", aplicarFiltros);
  if (fechaInput) fechaInput.addEventListener("change", aplicarFiltros);
  if (tipoSelect) tipoSelect.addEventListener("change", aplicarFiltros);
  if (maquinaSelect) maquinaSelect.addEventListener("change", aplicarFiltros);

  // Re-aplicar cuando se agreguen/quiten tarjetas dinámicamente
  var obs = new MutationObserver(aplicarFiltros);
  obs.observe(lista, { childList: true });
});
