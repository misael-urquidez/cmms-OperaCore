(function () {
  var dot = document.getElementById('elipseFootDot');
  var text = document.getElementById('elipseFootText');
  if (!dot || !text) return;

  var ENDPOINT = '/elipse/estado/';
  var INTERVALO = 30000;
  var checando = false;

  function marcar(ok, mensaje) {
    dot.classList.toggle('is-offline', !ok);
    text.textContent = mensaje;
  }

  function chequear() {
    if (checando) return;

    if (!navigator.onLine) {
      marcar(false, 'Sin conexión');
      return;
    }

    checando = true;
    var controller = new AbortController();
    var timeoutId = setTimeout(function () { controller.abort(); }, 5000);

    fetch(ENDPOINT, { signal: controller.signal, credentials: 'same-origin' })
      .then(function (resp) { return resp.json(); })
      .then(function (data) {
        marcar(!!data.ok, data.ok ? 'API conectada' : 'IA no disponible');
      })
      .catch(function () {
        marcar(false, 'IA no disponible');
      })
      .finally(function () {
        clearTimeout(timeoutId);
        checando = false;
      });
  }

  window.addEventListener('online', chequear);
  window.addEventListener('offline', function () { marcar(false, 'Sin conexión'); });

  chequear();
  setInterval(chequear, INTERVALO);
})();