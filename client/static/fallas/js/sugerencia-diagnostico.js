(function () {
  "use strict";
  var cfg = window.SUGERENCIA_IA_CONFIG || {};

  var maquinaSel = document.getElementById("maquina");
  var causaInput = document.getElementById("causaRaiz");
  var descInput = document.getElementById("descripcion");
  var severidadSel = document.getElementById("tipo_severidad");

  var box = document.getElementById("sugerenciaIA");
  var titulo = document.getElementById("sugerenciaIATitulo");
  var elCausa = document.getElementById("sugerenciaIACausa");
  var elJustif = document.getElementById("sugerenciaIAJustif");
  var btnUsar = document.getElementById("sugerenciaIAUsar");
  var btnCerrar = document.getElementById("sugerenciaIACerrar");

  if (!maquinaSel || !box || !cfg.url) return;

  var timer = null;
  var ultimaSugerencia = null;
  var ultimaFirma = "";

  var FUENTES = {
    ia: { etiqueta: "Sugerido por Elipse (IA)", clase: "ok" },
    historial_local: { etiqueta: "Sin conexión — basado en el historial de esta máquina", clase: "local" },
    consejo_general: { etiqueta: "Consejo general — esta máquina no tiene historial aún", clase: "generico" },
  };

  function sintomaActual() {
    return ((descInput && descInput.value) || "") + " " + ((causaInput && causaInput.value) || "");
  }

  function ocultar() {
    box.hidden = true;
  }

  function pedirSugerencia() {
    var maquina = maquinaSel.value;
    var sintoma = sintomaActual().trim();
    if (!maquina || sintoma.length < 12) {
      ocultar();
      return;
    }
    var firma = maquina + "|" + sintoma;
    if (firma === ultimaFirma) return; // ya se pidio esto mismo
    ultimaFirma = firma;

    box.hidden = false;
    box.className = "sugerencia-ia cargando";
    titulo.textContent = "Analizando historial de la máquina…";
    elCausa.textContent = "";
    elJustif.textContent = "";
    btnUsar.hidden = true;

    fetch(cfg.url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": cfg.csrf || "" },
      body: JSON.stringify({ maquina: maquina, sintoma: sintoma }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.error) { ocultar(); return; }
        ultimaSugerencia = data;
        var fuente = FUENTES[data.fuente] || FUENTES.consejo_general;
        box.className = "sugerencia-ia " + fuente.clase;
        titulo.textContent =
          (data.casos_similares > 0
            ? "Basado en " + data.casos_similares + " falla(s) previa(s) de esta máquina: "
            : "") + fuente.etiqueta;
        elCausa.textContent = data.causa_probable || "";
        elJustif.textContent = data.justificacion || "";
        btnUsar.hidden = false;
      })
      .catch(function () { ocultar(); });
  }

  function conDebounce() {
    clearTimeout(timer);
    timer = setTimeout(pedirSugerencia, 900);
  }

  maquinaSel.addEventListener("change", conDebounce);
  if (causaInput) causaInput.addEventListener("input", conDebounce);
  if (descInput) descInput.addEventListener("input", conDebounce);

  btnUsar.addEventListener("click", function () {
    if (!ultimaSugerencia) return;
    if (causaInput && !causaInput.value.trim()) {
      causaInput.value = ultimaSugerencia.causa_probable || "";
    }
    if (severidadSel && ultimaSugerencia.severidad) {
      severidadSel.value = ultimaSugerencia.severidad;
    }
    // el tecnico sigue pudiendo editar ambos campos a mano despues de esto
  });

  btnCerrar.addEventListener("click", ocultar);
})();