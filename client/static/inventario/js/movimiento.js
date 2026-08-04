function seleccionarTipo(el) {
  document.querySelectorAll('.tecni-stat-card').forEach(function(c) {
    c.style.outline = 'none';
  });
  el.style.outline = '2px solid var(--color-primary)';

  const tipo = el.getAttribute('data-tipo');
  document.getElementById('tipoMovimiento').value = tipo;
  document.getElementById('formulario-movimiento').style.display = 'block';

  const campoOrden = document.getElementById('campo-orden');
  const campoPieza = document.getElementById('campo-pieza');
  const campoRefaccion = document.getElementById('campo-refaccion');
  const campoDesc = document.getElementById('campo-descripcion');
  const selOrden = document.getElementById('mov-orden');
  const selPieza = document.getElementById('mov-pieza');
  const selRefaccion = document.getElementById('mov-refaccion');

  if (tipo === 'INSTA') {
    campoOrden.style.display = '';
    campoPieza.style.display = '';
    campoRefaccion.style.display = '';
    campoDesc.style.display = 'none';
    selOrden.required = true;
    selPieza.required = true;
    selRefaccion.required = true;
  } else if (tipo === 'DESMO') {
    campoOrden.style.display = '';
    campoPieza.style.display = '';
    campoRefaccion.style.display = 'none';
    campoDesc.style.display = '';
    selOrden.required = true;
    selPieza.required = true;
    selRefaccion.required = false;
    selRefaccion.value = '';
  } else if (tipo === 'REHA') {
    campoOrden.style.display = '';
    campoPieza.style.display = '';
    campoRefaccion.style.display = '';
    campoDesc.style.display = 'none';
    selOrden.required = false;
    selPieza.required = true;
    selRefaccion.required = true;
  }
}
