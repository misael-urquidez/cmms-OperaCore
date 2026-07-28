document.addEventListener('DOMContentLoaded', function () {
  document.getElementById('buscador').addEventListener('input', function () {
    const busqueda = this.value.toLowerCase();
    const tabla = document.getElementById('data-table');
    const filas = tabla.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
    for (let fila of filas) {
      const celdas = fila.getElementsByTagName('td');
      let encontrado = false;
      for (let celda of celdas) {
        if (celda.textContent.toLowerCase().includes(busqueda)) {
          encontrado = true;
          break;
        }
      }
      fila.style.display = encontrado ? '' : 'none';
    }
  });
});
