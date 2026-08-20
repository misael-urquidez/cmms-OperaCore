document.addEventListener("DOMContentLoaded", function () {
  var input = document.getElementById("trabBuscador");
  var grid = document.querySelector(".trab-grid");
  if (!input || !grid) return;

  function filtrar() {
    var texto = input.value.toLowerCase();
    var cards = grid.querySelectorAll(".trab-card");
    for (var i = 0; i < cards.length; i++) {
      var pass = !texto || cards[i].textContent.toLowerCase().indexOf(texto) !== -1;
      cards[i].style.display = pass ? "" : "none";
    }
  }

  input.addEventListener("input", filtrar);

  var obs = new MutationObserver(filtrar);
  obs.observe(grid, { childList: true });
});
