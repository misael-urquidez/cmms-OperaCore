(function () {
  const body = document.body;

  // ---------- Fondo animado (ondas + particulas) — valores de la maqueta ----------
  const canvas = document.getElementById("auth-waves");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  window.addEventListener("resize", resize);
  resize();

  const waves = [
    { l: 0.0035, a: 80, s: 0.0018, b: 0, phase: 0 },
    { l: 0.0055, a: 55, s: -0.0012, b: 2.1, phase: 1 },
    { l: 0.0025, a: 100, s: 0.001, b: 4.3, phase: 2 },
    { l: 0.006, a: 40, s: -0.0025, b: 1.2, phase: 3 },
    { l: 0.004, a: 65, s: 0.0016, b: 3.5, phase: 4 },
  ];

  const particles = Array.from({ length: 80 }, () => ({
    x: Math.random() * window.innerWidth,
    y: Math.random() * window.innerHeight,
    sz: Math.random() * 2 + 0.4,
    vx: (Math.random() - 0.5) * 0.06,
    vy: -(Math.random() * 0.12 + 0.02),
    a: Math.random() * 0.35 + 0.08,
  }));

  let tick = 0;
  let raf;

  function draw() {
    raf = requestAnimationFrame(draw);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    tick += 0.6;
    const cy = canvas.height * 0.52;

    waves.forEach((w, i) => {
      ctx.beginPath();
      ctx.strokeStyle = `rgba(140,195,255,${0.06 + i * 0.022})`;
      ctx.lineWidth = 2.5 + i * 0.6;
      ctx.shadowBlur = 18;
      ctx.shadowColor = "rgba(120,180,255,0.4)";
      for (let x = 0; x < canvas.width; x++) {
        const y =
          cy +
          Math.sin(x * w.l + tick * w.s + w.b) * w.a +
          Math.sin(x * 0.002 - tick * 0.0008 + w.phase) * 28 +
          Math.cos(x * 0.0008 + tick * 0.0005) * 18;
        x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.stroke();
    });

    ctx.shadowBlur = 0;
    particles.forEach((p) => {
      ctx.beginPath();
      ctx.fillStyle = `rgba(220,235,255,${p.a})`;
      ctx.arc(p.x, p.y, p.sz, 0, Math.PI * 2);
      ctx.fill();
      p.x += p.vx;
      p.y += p.vy;
      if (p.y < -10) {
        p.y = canvas.height + 10;
        p.x = Math.random() * canvas.width;
      }
      if (p.x < -10 || p.x > canvas.width + 10) {
        p.x = Math.random() * canvas.width;
      }
    });
  }
  draw();

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) cancelAnimationFrame(raf);
    else draw();
  });

  // ---------- Secuencia de encendido (boot) ----------
  const loginBox = document.getElementById("login-box");
  let phase = "boot";
  let seq = [];

  // Si venimos con errores/avisos o directo al registro, saltamos la intro.
  const hasMessages = !!document.querySelector(".auth-messages");
  const wantsRegistro = body.dataset.tab === "registro";
  const skipIntro = hasMessages || wantsRegistro;

  function revealBox() {
    loginBox.style.display = "block";
    requestAnimationFrame(() =>
      requestAnimationFrame(() => loginBox.classList.add("visible"))
    );
  }

  function showLogin() {
    if (phase === "login") return;
    phase = "login";
    seq.forEach((t) => clearTimeout(t));
    body.classList.remove("hint-in");
    body.classList.add("hint-out", "logo-out");
    setTimeout(revealBox, 900);
  }

  function runSequence() {
    seq.push(setTimeout(() => body.classList.add("awake"), 300));   // fondo + ondas
    seq.push(setTimeout(() => body.classList.add("logo-in"), 1800)); // logo CMMS
    seq.push(setTimeout(() => body.classList.add("hint-in"), 2600)); // hint
    seq.push(setTimeout(showLogin, 4800));                           // -> login
  }

  if (skipIntro) {
    body.classList.add("awake");
    phase = "login";
    revealBox();
  } else {
    runSequence();
    document.addEventListener("keydown", showLogin);
    document.addEventListener("click", showLogin);
    loginBox.addEventListener("click", (e) => e.stopPropagation());
    const hint = document.getElementById("skip-hint");
    if (hint) hint.addEventListener("click", showLogin);
  }

  // ---------- Alternar login <-> registro (enlaces dentro de la caja) ----------
  const forms = {
    login: document.getElementById("form-login"),
    registro: document.getElementById("form-registro"),
  };

  function activarForm(nombre) {
    Object.entries(forms).forEach(([key, form]) => {
      if (form) form.classList.toggle("auth-form--active", key === nombre);
    });
    const url = new URL(window.location);
    url.searchParams.set("tab", nombre);
    window.history.replaceState({}, "", url);
  }

  document.querySelectorAll(".auth-switch a[data-tab]").forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      activarForm(link.dataset.tab);
    });
  });

  // ---------- Validacion del formulario de registro ----------
  // Reglas coherentes con la BD (longitudes) y con el API (unicidad y fuerza
  // de contraseña las verifica el servidor; aqui cubrimos formato/requeridos).
  const formRegistro = document.getElementById("form-registro");
  if (formRegistro) {
    const NOMBRE_RE = /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ'’.\- ]+$/;
    const CORREO_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const USUARIO_RE = /^[A-Za-z0-9._-]+$/;
    const passInput = formRegistro.querySelector("#reg-password");
    const soloDigitos = (v) => v.replace(/\D/g, "");

    const reglas = {
      nombre: (v) =>
        !v ? "El nombre es obligatorio."
        : v.length > 50 ? "Máximo 50 caracteres."
        : !NOMBRE_RE.test(v) ? "Solo letras, espacios, guion o punto."
        : "",
      apellidoPat: (v) =>
        !v ? "El apellido paterno es obligatorio."
        : v.length > 50 ? "Máximo 50 caracteres."
        : !NOMBRE_RE.test(v) ? "Solo letras, espacios, guion o punto."
        : "",
      apellidoMat: (v) =>
        !v ? "" // opcional
        : v.length > 50 ? "Máximo 50 caracteres."
        : !NOMBRE_RE.test(v) ? "Solo letras, espacios, guion o punto."
        : "",
      telefono: (v) => {
        const d = soloDigitos(v);
        return !v ? "El teléfono es obligatorio."
          : d.length !== 10 ? "Ingresa 10 dígitos."
          : "";
      },
      correo: (v) =>
        !v ? "El correo es obligatorio."
        : v.length > 100 ? "Máximo 100 caracteres."
        : !CORREO_RE.test(v) ? "Correo no válido (ej. nombre@dominio.com)."
        : "",
      usuario: (v) =>
        !v ? "El usuario es obligatorio."
        : v.length < 3 ? "Mínimo 3 caracteres."
        : v.length > 30 ? "Máximo 30 caracteres."
        : !USUARIO_RE.test(v) ? "Solo letras, números y . _ - (sin espacios)."
        : "",
      password: (v) =>
        !v ? "La contraseña es obligatoria."
        : v.length < 8 ? "Mínimo 8 caracteres."
        : /^\d+$/.test(v) ? "No puede ser solo números."
        : "",
      password2: (v) =>
        !v ? "Confirma la contraseña."
        : v !== (passInput ? passInput.value : "") ? "Las contraseñas no coinciden."
        : "",
    };

    // Las contraseñas no se recortan; el resto de campos si (igual que el server).
    const esPassword = (name) => name === "password" || name === "password2";

    function errorSpan(input) {
      const wrap = input.closest(".inp-wrap");
      let span = wrap.querySelector(".inp-error");
      if (!span) {
        span = document.createElement("span");
        span.className = "inp-error";
        wrap.appendChild(span);
      }
      return span;
    }

    function validarCampo(input) {
      const regla = reglas[input.name];
      if (!regla) return true;
      const valor = esPassword(input.name) ? input.value : input.value.trim();
      const msg = regla(valor);
      errorSpan(input).textContent = msg;
      input.classList.toggle("is-invalid", !!msg);
      return !msg;
    }

    const campos = Object.keys(reglas)
      .map((name) => formRegistro.querySelector(`[name="${name}"]`))
      .filter(Boolean);

    campos.forEach((input) => {
      input.addEventListener("blur", () => validarCampo(input));   // valida al salir
      input.addEventListener("input", () => {                       // limpia mientras corrige
        if (input.classList.contains("is-invalid")) validarCampo(input);
      });
    });

    // Revalida la confirmacion cuando cambia la contraseña principal.
    const pass2 = formRegistro.querySelector("#reg-password2");
    if (passInput && pass2) {
      passInput.addEventListener("input", () => {
        if (pass2.classList.contains("is-invalid")) validarCampo(pass2);
      });
    }

    formRegistro.addEventListener("submit", (e) => {
      let ok = true;
      let primerError = null;
      campos.forEach((input) => {
        const valido = validarCampo(input);
        if (!valido && !primerError) primerError = input;
        ok = ok && valido;
      });
      if (!ok) {
        e.preventDefault();
        if (primerError) primerError.focus();
        return;
      }
      // Normaliza el telefono a 10 digitos limpios antes de enviar.
      const tel = formRegistro.querySelector('[name="telefono"]');
      if (tel) tel.value = soloDigitos(tel.value);

      // Evita el doble envio (que provocaba choques de numeroNomina):
      // deshabilita el boton en cuanto arranca el submit valido.
      const btn = formRegistro.querySelector(".btn-login");
      if (btn) {
        btn.disabled = true;
        btn.textContent = "Creando cuenta...";
      }
    });
  }
})();
