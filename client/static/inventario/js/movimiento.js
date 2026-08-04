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

  var modal = document.getElementById("newMachineModal");
  var form = document.getElementById("newMachineForm");
  var errorBox = document.getElementById("newMachineError");
  var catalogosCargados = false;

  document.getElementById("btnNuevaMaquina").addEventListener("click", function () {
    modal.setAttribute("aria-hidden", "false");
    if (!catalogosCargados) cargarCatalogos();
  });
  function cerrarModal() { modal.setAttribute("aria-hidden", "true"); errorBox.hidden = true; }
  document.getElementById("newMachineClose").addEventListener("click", cerrarModal);
  document.getElementById("newMachineCancel").addEventListener("click", cerrarModal);
  document.getElementById("newMachineBackdrop").addEventListener("click", cerrarModal);

  function llenarSelect(select, items, valueKey, labelKey, placeholder) {
    select.innerHTML = "";
    if (placeholder) {
      var opt0 = document.createElement("option");
      opt0.value = ""; opt0.textContent = placeholder;
      select.appendChild(opt0);
    }
    items.forEach(function (it) {
      var opt = document.createElement("option");
      opt.value = it[valueKey];
      opt.textContent = it[labelKey];
      if (it.marca !== undefined) opt.dataset.marca = it.marca;
      select.appendChild(opt);
    });
  }

  var todosLosModelos = [];
  function cargarCatalogos() {
    fetch(CATALOGOS_URL).then(function (r) { return r.json(); }).then(function (data) {
      catalogosCargados = true;
      llenarSelect(document.getElementById("fLinea"), data.lineas || [], "codigo", "nombre", "Selecciona línea");
      llenarSelect(document.getElementById("fTipo"), data.tipos_maquina || [], "numeroRegistro", "nombre", "Selecciona tipo");
      llenarSelect(document.getElementById("fMarca"), data.marcas || [], "clave", "nombre", "Selecciona marca");
      llenarSelect(document.getElementById("fEstado"), data.estados_maquina || [], "codigo", "nombre", "Selecciona estado");
      llenarSelect(document.getElementById("fModo"), data.modos_monitoreo || [], "valor", "etiqueta", "Selecciona modo");
      todosLosModelos = data.modelos || [];
      filtrarModelos("");
    }).catch(function () {
      errorBox.hidden = false;
      errorBox.textContent = "No se pudieron cargar los catálogos.";
    });
  }
  function filtrarModelos(marca) {
    var lista = marca ? todosLosModelos.filter(function (m) { return m.marca === marca; }) : todosLosModelos;
    llenarSelect(document.getElementById("fModelo"), lista, "codigo", "nombre", "Sin especificar");
  }
  document.getElementById("fMarca").addEventListener("change", function (ev) { filtrarModelos(ev.target.value); });

  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    errorBox.hidden = true;
    var payload = {
      codigo: document.getElementById("fCodigo").value.trim(),
      nombre: document.getElementById("fNombre").value.trim(),
      descripcion: document.getElementById("fDescripcion").value.trim(),
      numeroSerie: document.getElementById("fSerie").value.trim(),
      linea: document.getElementById("fLinea").value || null,
      marca: document.getElementById("fMarca").value || null,
      modelo: document.getElementById("fModelo").value || null,
      tipo_maquina: document.getElementById("fTipo").value || null,
      estado_maquina: document.getElementById("fEstado").value || null,
      modo_monitoreo: document.getElementById("fModo").value,
      umbral_vibracion: parseFloat(document.getElementById("fUmbral").value) || 4.0,
    };
    fetch(CREAR_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
      body: JSON.stringify(payload),
    }).then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
      .then(function (res) {
        if (!res.ok) {
          errorBox.hidden = false;
          errorBox.textContent = typeof res.data === "object" ? JSON.stringify(res.data) : "No se pudo crear la máquina.";
          return;
        }
        cerrarModal();
        form.reset();
        refrescar();
      }).catch(function () {
        errorBox.hidden = false;
        errorBox.textContent = "No fue posible conectar con el servidor.";
      });
  });
  var CREAR_ORDEN_URL = root.dataset.crearOrdenUrl;
  var btnLevantarOrden = document.getElementById("drawerLevantarOrden");
  if (btnLevantarOrden && CREAR_ORDEN_URL) {
    btnLevantarOrden.addEventListener("click", function () {
      if (!estado.seleccionada) return;
      var codigo = estado.seleccionada;
      fetch(CREAR_ORDEN_URL, { method:"POST", headers:{"Content-Type":"application/json", "X-CSRFToken":getCookie("csrftoken")}, body:JSON.stringify({maquina:codigo, tipo_mantenimiento:"PREVE", descripcion:"Revisión preventiva sugerida por tendencia de vibración en " + codigo + "."}) })
        .then(function(r){ return r.json().then(function(data){ return {ok:r.ok, data:data}; }); })
        .then(function(res){ var msg=document.getElementById("drawerOrdenMsg"); mostrarMsg(msg, res.ok ? "Orden " + res.data.folio + " creada. Asígnala desde Mantenimiento." : "No se pudo levantar la orden.", res.ok); })
        .catch(function(){ mostrarMsg(document.getElementById("drawerOrdenMsg"), "No fue posible conectar con el servidor.", false); });
    });
  }