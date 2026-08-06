function seleccionarTipo(el) {
  document.querySelectorAll('.tecni-stat-card').forEach(function(c) {
    c.style.outline = 'none';
  });
  el.style.outline = '2px solid var(--color-primary)';

  var tipo = el.getAttribute('data-tipo');
  document.getElementById('tipoMovimiento').value = tipo;
  document.getElementById('formulario-movimiento').style.display = 'block';

  var campoOrden = document.getElementById('campo-orden');
  var campoRefaccion = document.getElementById('campo-refaccion');
  var campoDesc = document.getElementById('campo-descripcion');
  var selOrden = document.getElementById('mov-orden');
  var selRefaccion = document.getElementById('mov-refaccion');

  if (tipo === 'INSTA') {
    campoOrden.style.display = '';
    campoRefaccion.style.display = '';
    campoDesc.style.display = 'none';
    selOrden.required = true;
    selRefaccion.required = true;
  } else if (tipo === 'DESMO') {
    campoOrden.style.display = '';
    campoRefaccion.style.display = 'none';
    campoDesc.style.display = '';
    selOrden.required = true;
    selRefaccion.required = false;
    selRefaccion.value = '';
  } else if (tipo === 'REHA') {
    campoOrden.style.display = '';
    campoRefaccion.style.display = '';
    campoDesc.style.display = 'none';
    selOrden.required = false;
    selRefaccion.required = true;
  }

  limpiarPieza();

  // INSTA: se elige la pieza con el modal (existente o nueva).
  // DESMO/REHA: solo select de piezas existentes (sin registro).
  var wrapNueva = document.getElementById('pieza-nueva-wrap');
  var selectPieza = document.getElementById('mov-pieza-select');
  var resumenPieza = document.getElementById('mov-pieza-resumen');
  if (tipo === 'INSTA') {
    if (wrapNueva) wrapNueva.style.display = '';
    if (selectPieza) { selectPieza.style.display = 'none'; selectPieza.value = ''; }
    if (resumenPieza) resumenPieza.style.display = '';
  } else {
    if (wrapNueva) wrapNueva.style.display = 'none';
    if (selectPieza) selectPieza.style.display = '';
    if (resumenPieza) resumenPieza.style.display = 'none';
    if (selectPieza) document.getElementById('mov-pieza').value = selectPieza.value;
  }
}

/* ---- limpieza de pieza (global: se usa tambien desde seleccionarTipo) ---- */
function limpiarPieza() {
  var hid = document.getElementById('mov-pieza');
  if (hid) hid.value = '';
  document.querySelectorAll('#mov-pieza-modal [name^="pieza_"]').forEach(function(inp) {
    inp.value = '';
  });
  var resumen = document.getElementById('mov-pieza-resumen');
  if (resumen) resumen.textContent = 'Sin pieza seleccionada.';
}

/* ---- modal de pieza (existente o nueva) ---- */
(function () {
  var modal = document.getElementById('mov-pieza-modal');
  if (!modal) return;

  function leerJson(id) {
    var el = document.getElementById(id);
    if (!el) return [];
    try { return JSON.parse(el.textContent); } catch (e) { return []; }
  }

  var PIEZAS = leerJson('mov-piezas-data');
  var ORDENES = leerJson('mov-ordenes-data');
  var REFACCIONES = leerJson('mov-refacciones-data');

  var lista = document.getElementById('mov-pieza-lista');
  var buscar = document.getElementById('mov-pieza-buscar');
  var resumen = document.getElementById('mov-pieza-resumen');

  function abrirModalPieza() {
    prefilarDesdeRefaccion();
    activarTab('buscar');
    pintarListaPiezas();
    modal.classList.add('is-open');
  }

  function cerrarModalPieza() {
    modal.classList.remove('is-open');
  }

  function activarTab(nombre) {
    document.querySelectorAll('.mov-pieza__tab').forEach(function(b) {
      b.classList.toggle('is-active', b.getAttribute('data-tab') === nombre);
    });
    document.querySelectorAll('.mov-pieza__panel').forEach(function(p) {
      p.hidden = p.getAttribute('data-panel') !== nombre;
    });
    var btnRegistrar = document.getElementById('mov-pieza-registrar');
    if (btnRegistrar) btnRegistrar.hidden = nombre !== 'nueva';
  }

  function pintarListaPiezas() {
    if (!lista) return;
    lista.innerHTML = '';
    var q = (buscar && buscar.value || '').toLowerCase().trim();
    var filtradas = PIEZAS.filter(function(p) {
      if (!q) return true;
      return (p.numeroserie || '').toLowerCase().indexOf(q) !== -1 ||
             (p.nombre || '').toLowerCase().indexOf(q) !== -1;
    });
    if (!filtradas.length) {
      var vacio = document.createElement('p');
      vacio.style.cssText = 'font-size:.85rem;opacity:.7;margin:0;';
      vacio.textContent = 'No se encontraron piezas. Usa la pestaña "Registrar nueva".';
      lista.appendChild(vacio);
      return;
    }
    filtradas.forEach(function(p) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'mov-pieza__item';
      var strong = document.createElement('strong');
      strong.textContent = p.nombre || 'Pieza';
      var span = document.createElement('span');
      span.textContent = p.numeroserie || '';
      btn.appendChild(strong);
      btn.appendChild(span);
      btn.addEventListener('click', function() { seleccionarPiezaExistente(p); });
      lista.appendChild(btn);
    });
  }

  function seleccionarPiezaExistente(p) {
    limpiarCamposNueva();
    document.getElementById('mov-pieza').value = p.numeroserie || '';
    resumen.textContent = 'Pieza seleccionada: ' + (p.nombre || '') + ' — ' + (p.numeroserie || '');
    cerrarModalPieza();
  }

  function limpiarCamposNueva() {
    document.querySelectorAll('#mov-pieza-modal [name^="pieza_"]').forEach(function(inp) {
      inp.value = '';
    });
  }

  // En INSTA, la pieza "nace" de la refaccion a instalar: se precargan
  // nombre y costo inicial a partir de la refaccion seleccionada.
  function prefilarDesdeRefaccion() {
    var tipo = document.getElementById('tipoMovimiento').value;
    if (tipo !== 'INSTA') return;
    var selRef = document.getElementById('mov-refaccion');
    if (!selRef || !selRef.value) return;
    var ref = REFACCIONES.filter(function(r) { return String(r.numeroregistro) === String(selRef.value); })[0];
    if (!ref) return;
    var campoNombre = document.getElementById('pieza_nombre');
    var campoCosto = document.getElementById('pieza_costoinicial');
    if (campoNombre && !campoNombre.value && ref.nombre) campoNombre.value = ref.nombre;
    if (campoCosto && !campoCosto.value && ref.costo) campoCosto.value = ref.costo;
  }

  /* ---- wiring ---- */
  var btnAbrir = document.getElementById('mov-pieza-btn');
  if (btnAbrir) btnAbrir.addEventListener('click', abrirModalPieza);
  if (buscar) buscar.addEventListener('input', pintarListaPiezas);

  // DESMO/REHA: el select de existentes alimenta el hidden "pieza".
  var selectPieza = document.getElementById('mov-pieza-select');
  if (selectPieza) {
    selectPieza.addEventListener('change', function() {
      document.getElementById('mov-pieza').value = selectPieza.value;
      if (resumen && selectPieza.value) {
        var opt = selectPieza.selectedOptions && selectPieza.selectedOptions[0];
        resumen.textContent = 'Pieza seleccionada: ' + (opt ? opt.textContent : selectPieza.value);
      }
    });
  }

  var btnCerrar = document.getElementById('mov-pieza-modal-close');
  if (btnCerrar) btnCerrar.addEventListener('click', cerrarModalPieza);
  var btnCancelar = document.getElementById('mov-pieza-modal-cancelar');
  if (btnCancelar) btnCancelar.addEventListener('click', cerrarModalPieza);
  var backdrop = modal.querySelector('.fallas-modal__backdrop');
  if (backdrop) backdrop.addEventListener('click', cerrarModalPieza);

  document.querySelectorAll('.mov-pieza__tab').forEach(function(tab) {
    tab.addEventListener('click', function() { activarTab(tab.getAttribute('data-tab')); });
  });

  // "Usar pieza nueva": los campos del modal se guardan en los inputs
  // pieza_* del formulario; la pieza se creara en el API al registrar el
  // movimiento (en la misma transaccion).
  var btnRegistrar = document.getElementById('mov-pieza-registrar');
  if (btnRegistrar) {
    btnRegistrar.addEventListener('click', function() {
      var requeridos = [
        ['pieza_numeroserie', 'Número de serie'],
        ['pieza_nombre', 'Nombre de la pieza'],
        ['pieza_costoinicial', 'Costo inicial'],
        ['pieza_tiempovidautil', 'Vida útil estimada'],
        ['pieza_tipo_pieza', 'Tipo de pieza'],
        ['pieza_edo_pieza', 'Estado físico/operativo'],
      ];
      for (var i = 0; i < requeridos.length; i++) {
        var f = document.getElementById(requeridos[i][0]);
        if (!f || !f.value) {
          alert('Completa el campo obligatorio: ' + requeridos[i][1]);
          return;
        }
      }
      document.getElementById('mov-pieza').value = '';
      var nombre = document.getElementById('pieza_nombre').value;
      resumen.textContent = 'Pieza nueva: ' + nombre + ' (se registrará al guardar el movimiento)';
      cerrarModalPieza();
    });
  }

  // La maquina de la pieza nueva se deduce de la orden seleccionada.
  var selOrden = document.getElementById('mov-orden');
  if (selOrden) {
    selOrden.addEventListener('change', function() {
      var folio = selOrden.value;
      var orden = ORDENES.filter(function(o) { return o.folio === folio; })[0];
      if (orden && orden.maquina) {
        var selMaquina = document.getElementById('pieza_maquina');
        if (selMaquina) selMaquina.value = orden.maquina;
      }
    });
  }

  // Validacion: hace falta pieza existente o pieza nueva registrada.
  var form = document.getElementById('form-movimiento');
  if (form) {
    form.addEventListener('submit', function(e) {
      var piezaPk = document.getElementById('mov-pieza').value;
      var tieneNueva = Array.prototype.some.call(
        document.querySelectorAll('#mov-pieza-modal [name^="pieza_"]'),
        function(inp) { return inp.value; }
      );
      if (!piezaPk && !tieneNueva) {
        e.preventDefault();
        alert('Selecciona o registra una pieza antes de registrar el movimiento.');
      }
    });
  }
})();
