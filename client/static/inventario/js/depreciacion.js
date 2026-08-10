(function () {
  "use strict";

  function getCookie(nombre) {
    var valor = null;
    if (document.cookie && document.cookie !== "") {
      document.cookie.split(";").forEach(function (c) {
        c = c.trim();
        if (c.substring(0, nombre.length + 1) === nombre + "=") {
          valor = decodeURIComponent(c.substring(nombre.length + 1));
        }
      });
    }
    return valor;
  }

  document.addEventListener("click", function (e) {
    var btn = e.target.closest(".inv-drawer__dep-calc-btn");
    if (!btn) return;

    var numeroSerie = btn.dataset.pieza;
    var fila = btn.closest(".inv-drawer__dep-calc");
    var input = fila.querySelector(".inv-drawer__dep-calc-input");
    var msg = fila.querySelector(".inv-drawer__dep-calc-msg");
    var tasa = parseFloat(input.value);

    msg.textContent = "";
    msg.className = "inv-drawer__dep-calc-msg";

    if (!tasa || tasa <= 0) {
      msg.textContent = "Ingresa una tasa válida.";
      msg.classList.add("inv-drawer__dep-calc-msg--error");
      return;
    }

    btn.disabled = true;
    fetch("/inventario/piezas/" + numeroSerie + "/depreciacion/", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
      body: JSON.stringify({ tasa: tasa }),
    })
      .then(function (res) {
        return res.json().then(function (data) { return { ok: res.ok, data: data }; });
      })
      .then(function (r) {
        btn.disabled = false;
        if (!r.ok) {
          msg.textContent = r.data.detail || "No se pudo calcular.";
          msg.classList.add("inv-drawer__dep-calc-msg--error");
          return;
        }
        msg.textContent = "Guardado: $" + r.data.depreciacionAnual + "/año";
        msg.classList.add("inv-drawer__dep-calc-msg--ok");

        // Refleja el nuevo valor en la etiqueta que ya pinta lista_pieza.html.
        var row = fila.closest(".inv-drawer__pieza-row");
        var depLabel = row && row.querySelector(".inv-drawer__pieza-dep");
        if (depLabel) {
          var costoTexto = depLabel.textContent.split("→")[0].trim();
          depLabel.textContent = costoTexto + " → $" + r.data.depreciacionAnual + "/año (SP)";
        }
      })
      .catch(function () {
        btn.disabled = false;
        msg.textContent = "Error de conexión.";
        msg.classList.add("inv-drawer__dep-calc-msg--error");
      });
  });
})();