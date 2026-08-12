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

  if (tipo === 'INSTA') {
    campoOrden.style.display = '';
    campoRefaccion.style.display = '';
    campoDesc.style.display = 'none';
    selOrden.required = true;
  } else if (tipo === 'DESMO') {
    campoOrden.style.display = '';
    campoRefaccion.style.display = 'none';
    campoDesc.style.display = '';
    selOrden.required = true;
    limpiarRefaccion();
  } else if (tipo === 'REHA') {
    campoOrden.style.display = '';
    campoRefaccion.style.display = 'none';
    campoDesc.style.display = 'none';
    selOrden.required = false;
    limpiarRefaccion();
  }

  limpiarPieza();

  // INSTA: se registra la pieza nueva con el modal (solo "Registrar nueva").
  // DESMO/REHA: select de piezas existentes, filtrado por estado
  // (DESMO -> instaladas, REHA -> en rehabilitacion).
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
    filtrarPiezasPorTipo(selectPieza, tipo);
    if (selectPieza) document.getElementById('mov-pieza').value = selectPieza.value;
  }
}

/* ---- filtro del select de piezas segun el tipo de movimiento ----
   DESMO: solo piezas instaladas en una maquina.
   REHA:  solo piezas en estado ENREH (en rehabilitacion). */
function filtrarPiezasPorTipo(select, tipo) {
  if (!select) return;
  Array.prototype.forEach.call(select.options, function(opt) {
    if (!opt.value) return;
    var estado = opt.getAttribute('data-estado') || '';
    var maquina = opt.getAttribute('data-maquina') || '';
    var ok = true;
    if (tipo === 'DESMO') ok = maquina !== '';
    else if (tipo === 'REHA') ok = estado === 'ENREH';
    opt.hidden = !ok;
  });
  if (select.value) {
    var sel = select.selectedOptions && select.selectedOptions[0];
    if (sel && sel.hidden) { select.value = ''; document.getElementById('mov-pieza').value = ''; }
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

/* ---- limpieza de refaccion (global: se usa tambien desde seleccionarTipo) ---- */
function limpiarRefaccion() {
  var hid = document.getElementById('mov-refaccion');
  if (hid) hid.value = '';
  document.querySelectorAll('#mov-refaccion-modal [name^="refaccion_"]').forEach(function(inp) {
    inp.value = '';
  });
  var resumen = document.getElementById('mov-refaccion-resumen');
  if (resumen) resumen.textContent = 'Sin refacción seleccionada.';
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
    activarTab('nueva');
    pintarListaPiezas();
    modal.classList.add('is-open');
  }

  function cerrarModalPieza() {
    modal.classList.remove('is-open');
  }

  function activarTab(nombre) {
    modal.querySelectorAll('.mov-pieza__tab').forEach(function(b) {
      b.classList.toggle('is-active', b.getAttribute('data-tab') === nombre);
    });
    modal.querySelectorAll('.mov-pieza__panel').forEach(function(p) {
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

  modal.querySelectorAll('.mov-pieza__tab').forEach(function(tab) {
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

/* ---- modal de refaccion (existente o nueva) ---- */
(function () {
  var modal = document.getElementById('mov-refaccion-modal');
  if (!modal) return;

  function leerJson(id) {
    var el = document.getElementById(id);
    if (!el) return [];
    try { return JSON.parse(el.textContent); } catch (e) { return []; }
  }

  var REFACCIONES = leerJson('mov-refacciones-data');

  var lista = document.getElementById('mov-refaccion-lista');
  var buscar = document.getElementById('mov-refaccion-buscar');
  var resumen = document.getElementById('mov-refaccion-resumen');

  function abrirModalRefaccion() {
    activarTab('buscar');
    pintarListaRefacciones();
    modal.classList.add('is-open');
  }

  function cerrarModalRefaccion() {
    modal.classList.remove('is-open');
  }

  function activarTab(nombre) {
    modal.querySelectorAll('.mov-pieza__tab').forEach(function(b) {
      b.classList.toggle('is-active', b.getAttribute('data-tab') === nombre);
    });
    modal.querySelectorAll('.mov-pieza__panel').forEach(function(p) {
      p.hidden = p.getAttribute('data-panel') !== nombre;
    });
    var btnRegistrar = document.getElementById('mov-refaccion-registrar');
    if (btnRegistrar) btnRegistrar.hidden = nombre !== 'nueva';
  }

  function pintarListaRefacciones() {
    if (!lista) return;
    lista.innerHTML = '';
    var q = (buscar && buscar.value || '').toLowerCase().trim();
    var filtradas = REFACCIONES.filter(function(r) {
      if (!q) return true;
      return (r.codigosku || '').toLowerCase().indexOf(q) !== -1 ||
             (r.nombre || '').toLowerCase().indexOf(q) !== -1 ||
             String(r.numeroregistro).indexOf(q) !== -1;
    });
    if (!filtradas.length) {
      var vacio = document.createElement('p');
      vacio.style.cssText = 'font-size:.85rem;opacity:.7;margin:0;';
      vacio.textContent = 'No se encontraron refacciones. Usa la pestaña "Registrar nueva".';
      lista.appendChild(vacio);
      return;
    }
    filtradas.forEach(function(r) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'mov-pieza__item';
      var strong = document.createElement('strong');
      strong.textContent = r.nombre || 'Refacción';
      var span = document.createElement('span');
      span.textContent = (r.codigosku || '') + ' · Stock: ' + (r.stock != null ? r.stock : '—');
      btn.appendChild(strong);
      btn.appendChild(span);
      btn.addEventListener('click', function() { seleccionarRefaccionExistente(r); });
      lista.appendChild(btn);
    });
  }

  function seleccionarRefaccionExistente(r) {
    limpiarCamposNueva();
    document.getElementById('mov-refaccion').value = r.numeroregistro;
    resumen.textContent = 'Refacción seleccionada: ' + (r.nombre || '') + ' — ' + (r.codigosku || '');
    cerrarModalRefaccion();
  }

  function limpiarCamposNueva() {
    document.querySelectorAll('#mov-refaccion-modal [name^="refaccion_"]').forEach(function(inp) {
      inp.value = '';
    });
  }

  /* ---- wiring ---- */
  var btnAbrir = document.getElementById('mov-refaccion-btn');
  if (btnAbrir) btnAbrir.addEventListener('click', abrirModalRefaccion);
  if (buscar) buscar.addEventListener('input', pintarListaRefacciones);

  var btnCerrar = document.getElementById('mov-refaccion-modal-close');
  if (btnCerrar) btnCerrar.addEventListener('click', cerrarModalRefaccion);
  var btnCancelar = document.getElementById('mov-refaccion-modal-cancelar');
  if (btnCancelar) btnCancelar.addEventListener('click', cerrarModalRefaccion);
  var backdrop = modal.querySelector('.fallas-modal__backdrop');
  if (backdrop) backdrop.addEventListener('click', cerrarModalRefaccion);

  modal.querySelectorAll('.mov-pieza__tab').forEach(function(tab) {
    tab.addEventListener('click', function() { activarTab(tab.getAttribute('data-tab')); });
  });

  // "Usar refaccion nueva": los campos refaccion_* del modal se guardan en el
  // formulario; la refaccion se creara en el API al registrar el movimiento.
  var btnRegistrar = document.getElementById('mov-refaccion-registrar');
  if (btnRegistrar) {
    btnRegistrar.addEventListener('click', function() {
      var requeridos = [
        ['refaccion_codigosku', 'Código SKU'],
        ['refaccion_nombre', 'Nombre'],
      ];
      for (var i = 0; i < requeridos.length; i++) {
        var f = document.getElementById(requeridos[i][0]);
        if (!f || !f.value) {
          alert('Completa el campo obligatorio: ' + requeridos[i][1]);
          return;
        }
      }
      document.getElementById('mov-refaccion').value = '';
      var nombre = document.getElementById('refaccion_nombre').value;
      resumen.textContent = 'Refacción nueva: ' + nombre + ' (se registrará al guardar el movimiento)';
      cerrarModalRefaccion();
    });
  }
})();
