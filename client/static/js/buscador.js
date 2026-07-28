document.addEventListener('DOMContentLoaded', function () {
  var busqueda = document.getElementById('buscador');
  var selects = document.querySelectorAll('.inv-search__select');

  function aplicarFiltros() {
    var texto = busqueda ? busqueda.value.toLowerCase() : '';

    var filtros = {};
    selects.forEach(function (sel) {
      var key = sel.getAttribute('data-filter');
      if (key && sel.value) filtros[key] = sel.value;
    });

    var tabla = document.getElementById('data-table');
    var filas = tabla.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

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
        var celdas = fila.getElementsByTagName('td');
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

  if (busqueda) busqueda.addEventListener('input', aplicarFiltros);
  selects.forEach(function (sel) {
    sel.addEventListener('change', aplicarFiltros);
  });
});
