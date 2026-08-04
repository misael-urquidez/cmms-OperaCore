function initBuscador(container) {
  var input = container.querySelector('.buscador-input, #buscador');
  var selects = container.querySelectorAll('.filter-select, .inv-search__select');
  var tablaSelector = container.getAttribute('data-buscador-target');
  var tabla = tablaSelector ? document.querySelector(tablaSelector) : document.getElementById('data-table');

  function aplicarFiltros() {
    var texto = input ? input.value.toLowerCase() : '';
    var filtros = {};
    selects.forEach(function (sel) {
      var key = sel.getAttribute('data-filter');
      if (key && sel.value) filtros[key] = sel.value;
    });
    if (!tabla) return;
    var tbody = tabla.querySelector('tbody');
    if (!tbody) return;
    var filas = tbody.querySelectorAll('tr');
    for (var i = 0; i < filas.length; i++) {
      var fila = filas[i];
      var pass = true;
      for (var key in filtros) {
        if (fila.getAttribute('data-' + key) !== filtros[key]) {
          pass = false;
          break;
        }
      }
      if (pass && texto) {
        pass = false;
        var celdas = fila.querySelectorAll('td');
        for (var j = 0; j < celdas.length; j++) {
          if (celdas[j].textContent.toLowerCase().indexOf(texto) !== -1) {
            pass = true;
            break;
          }
        }
      }
      fila.style.display = pass ? '' : 'none';
    }
  }

  if (input) input.addEventListener('input', aplicarFiltros);
  selects.forEach(function (sel) {
    sel.addEventListener('change', aplicarFiltros);
  });
}

document.addEventListener('DOMContentLoaded', function () {
  var containers = document.querySelectorAll('[data-buscador-target]');
  containers.forEach(function (c) { initBuscador(c); });
});
