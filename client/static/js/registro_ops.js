(function () {
  var select = document.getElementById('maquinaSelect');
  var tbody = document.getElementById('opsTableBody');
  var msg = document.getElementById('opsMsg');

  function getCookie(nombre) {
    var c = document.cookie.match('(^|;)\\s*' + nombre + '\\s*=\\s*([^;]+)');
    return c ? c.pop() : '';
  }

  function showMsg(text, type) {
    msg.textContent = text;
    msg.className = 'feedback-msg is-' + type;
    msg.hidden = false;
    setTimeout(function () { msg.hidden = true; }, 4000);
    if (window.mostrarToast) mostrarToast(text, type === 'is-ok' ? 'success' : 'error');
  }

  function buildRow(r) {
    var tr = document.createElement('tr');
    tr.dataset.pk = r.numeroRegistro;
    tr.innerHTML =
      '<td>' + r.numeroRegistro + '</td>' +
      '<td class="ops-view-cell">' +
        '<span class="ops-view" data-field="fechaInicio">' + r.fechaInicio + '</span>' +
        '<input class="ops-edit-input ops-edit" data-field="fechaInicio" type="date" value="' + r.fechaInicio + '">' +
      '</td>' +
      '<td class="ops-view-cell">' +
        '<span class="ops-view" data-field="fechaFin">' + r.fechaFin + '</span>' +
        '<input class="ops-edit-input ops-edit" data-field="fechaFin" type="date" value="' + r.fechaFin + '">' +
      '</td>' +
      '<td class="ops-view-cell">' +
        '<span class="ops-view" data-field="horasOperacion">' + r.horasOperacion + '</span>' +
        '<input class="ops-edit-input ops-edit" data-field="horasOperacion" type="number" step="1" min="0" value="' + r.horasOperacion + '">' +
      '</td>' +
      '<td><div class="ops-actions">' +
        '<button type="button" class="btn-icon btn-edit" title="Editar">✎</button>' +
        '<button type="button" class="btn-icon btn-save ops-edit" title="Guardar" hidden>✓</button>' +
        '<button type="button" class="btn-icon btn-danger btn-delete" title="Eliminar">✕</button>' +
      '</div></td>';
    return tr;
  }

  function loadRegistros(codigo) {
    var url = '/monitoreo/maquinas/' + codigo + '/registro-ops/';
    fetch(url)
      .then(function (res) { return res.json(); })
      .then(function (data) {
        tbody.innerHTML = '';
        if (!Array.isArray(data) || data.length === 0) {
          tbody.innerHTML = '<tr><td colspan="5" class="ops-empty">Sin registros de operación.</td></tr>';
          return;
        }
        data.forEach(function (r) {
          tbody.appendChild(buildRow(r));
        });
      })
      .catch(function () {
        tbody.innerHTML = '<tr><td colspan="5" class="ops-empty">Error al cargar registros.</td></tr>';
      });
  }

  select.addEventListener('change', function () {
    var codigo = select.value;
    if (!codigo) {
      tbody.innerHTML = '<tr><td colspan="5" class="ops-empty">Selecciona una máquina para ver sus registros.</td></tr>';
      return;
    }
    loadRegistros(codigo);
  });

  tbody.addEventListener('click', function (e) {
    var tr = e.target.closest('tr');
    if (!tr || !tr.dataset.pk) return;
    var pk = tr.dataset.pk;

    if (e.target.classList.contains('btn-edit')) {
      tr.querySelectorAll('.ops-view').forEach(function (el) { el.classList.add('is-hidden'); });
      tr.querySelectorAll('.ops-edit').forEach(function (el) { el.classList.add('is-editing'); });
      e.target.hidden = true;
    }

    if (e.target.classList.contains('btn-save')) {
      var fechaInicio = tr.querySelector('[data-field="fechaInicio"].ops-edit-input').value;
      var fechaFin = tr.querySelector('[data-field="fechaFin"].ops-edit-input').value;
      var horas = tr.querySelector('[data-field="horasOperacion"].ops-edit-input').value;

      var payload = {};
      if (fechaInicio) payload.fechaInicio = fechaInicio;
      if (fechaFin) payload.fechaFin = fechaFin;
      if (horas !== '') payload.horasOperacion = horas;

      var url = '/monitoreo/registro-ops/' + pk + '/';
      fetch(url, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify(payload),
      })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          if (data.numeroRegistro) {
            showMsg('Registro actualizado correctamente.', 'success');
            loadRegistros(select.value);
          } else {
            showMsg(data.detail || 'Error al actualizar.', 'error');
          }
        })
        .catch(function () {
          showMsg('Error de conexión.', 'error');
        });
    }

    if (e.target.classList.contains('btn-delete')) {
      if (!confirm('¿Eliminar este registro de operación?')) return;
      var url = '/monitoreo/registro-ops/' + pk + '/delete/';
      fetch(url, { method: 'DELETE', headers: { 'X-CSRFToken': getCookie('csrftoken') } })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          if (data.detail === 'Registro eliminado.') {
            showMsg('Registro eliminado.', 'success');
            loadRegistros(select.value);
          } else {
            showMsg(data.detail || 'Error al eliminar.', 'error');
          }
        })
        .catch(function () {
          showMsg('Error de conexión.', 'error');
        });
    }
  });
})();