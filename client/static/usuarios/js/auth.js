(function () {
  const body = document.body;

  // ---------- Utilidades de color (para el selector RGB libre) ----------
  function hexToHsl(hex) {
    const m = hex.replace("#", "");
    const r = parseInt(m.substring(0, 2), 16) / 255;
    const g = parseInt(m.substring(2, 4), 16) / 255;
    const b = parseInt(m.substring(4, 6), 16) / 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b);
    let h = 0, s = 0;
    const l = (max + min) / 2;
    const d = max - min;
    if (d !== 0) {
      s = d / (1 - Math.abs(2 * l - 1));
      switch (max) {
        case r: h = ((g - b) / d) % 6; break;
        case g: h = (b - r) / d + 2; break;
        default: h = (r - g) / d + 4;
      }
      h *= 60;
      if (h < 0) h += 360;
    }
    return { h, s: s * 100, l: l * 100 };
  }
  function hslToHex(h, s, l) {
    s /= 100; l /= 100;
    const c = (1 - Math.abs(2 * l - 1)) * s;
    const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
    const m = l - c / 2;
    let r = 0, g = 0, b = 0;
    if (h < 60) [r, g, b] = [c, x, 0];
    else if (h < 120) [r, g, b] = [x, c, 0];
    else if (h < 180) [r, g, b] = [0, c, x];
    else if (h < 240) [r, g, b] = [0, x, c];
    else if (h < 300) [r, g, b] = [x, 0, c];
    else [r, g, b] = [c, 0, x];
    const toHex = (v) =>
      Math.round((v + m) * 255).toString(16).padStart(2, "0");
    return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
  }

  // A partir de UN color elegido (input type="color"), deriva los 3 tonos
  // del degradado atmosférico + el acento usado en el tema "Plano".
  function applyColorVars(hex) {
    if (!hex) {
      ["--bg-g1", "--bg-g2", "--bg-g3", "--bg-base", "--accent"].forEach((v) =>
        body.style.removeProperty(v)
      );
      return;
    }
    const { h, s } = hexToHsl(hex);
    body.style.setProperty("--bg-g1", hslToHex(h, Math.min(s, 72), 32));
    body.style.setProperty("--bg-g2", hslToHex(h, Math.min(s, 60), 17));
    body.style.setProperty("--bg-g3", hslToHex(h, Math.min(s, 55), 5));
    body.style.setProperty("--bg-base", hslToHex(h, Math.min(s, 50), 3));
    body.style.setProperty("--accent", hex);
  }

  // ---------- Aplica preferencias guardadas ANTES del primer paint ----------
  const STORAGE_KEY_LINES = "operacore-auth-lines";
  const STORAGE_KEY_BG = "operacore-auth-bg";
  const STORAGE_KEY_COLOR = "operacore-auth-color";
  const STORAGE_KEY_STYLE = "operacore-auth-style";
  const STORAGE_KEY_BOOT = "operacore-auth-boot";

  let savedColor = "";
  try {
    const savedStyle = localStorage.getItem(STORAGE_KEY_STYLE);
    const savedBg = localStorage.getItem(STORAGE_KEY_BG);
    const savedLines = localStorage.getItem(STORAGE_KEY_LINES);
    const savedBoot = localStorage.getItem(STORAGE_KEY_BOOT);
    savedColor = localStorage.getItem(STORAGE_KEY_COLOR) || "";
    if (savedStyle === "plano" || savedStyle === "atmosferico") body.dataset.style = savedStyle;
    if (savedBg === "blue" || savedBg === "smt") body.dataset.bg = savedBg;
    if (savedLines === "classic" || savedLines === "smt") body.dataset.lines = savedLines;
    if (savedBoot === "on" || savedBoot === "off") body.dataset.boot = savedBoot;
    if (savedColor) applyColorVars(savedColor);
  } catch (e) {
    // localStorage bloqueado (modo privado, etc.): seguimos con los
    // defaults del HTML (data-bg="blue" data-lines="classic" data-boot="on")
    // sin romper.
  }

  // ---------- Fondo animado: dos lenguajes intercambiables ----------
  // "classic"  = ondas + partículas flotantes (la maqueta original).
  // "smt"      = carriles punteados + componentes en tránsito.
  // (No corre en absoluto si el tema activo es "plano".)
  const canvas = document.getElementById("auth-waves");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  window.addEventListener("resize", resize);
  resize();

  const WAVE_PRESETS = {
    classic: {
      waves: [
        { l: 0.0035, a: 80, s: 0.0018, b: 0, phase: 0 },
        { l: 0.0055, a: 55, s: -0.0012, b: 2.1, phase: 1 },
        { l: 0.0025, a: 100, s: 0.001, b: 4.3, phase: 2 },
        { l: 0.006, a: 40, s: -0.0025, b: 1.2, phase: 3 },
        { l: 0.004, a: 65, s: 0.0016, b: 3.5, phase: 4 },
      ],
      dashed: false,
      lineColor: (i) => `rgba(140, 195, 255, ${0.06 + i * 0.022})`,
      lineWidth: (i) => 2.5 + i * 0.6,
      shadowBlur: 18,
      shadowColor: "rgba(120, 180, 255, 0.4)",
      particleColor: (a) => `rgba(220, 235, 255, ${a})`,
    },
    smt: {
      waves: [
        { l: 0.0042, a: 14, s: 0.0018, b: 0, phase: 0 },
        { l: 0.0054, a: 10, s: -0.0012, b: 2.1, phase: 1 },
        { l: 0.0031, a: 18, s: 0.001, b: 4.3, phase: 2 },
        { l: 0.0062, a: 8, s: -0.0025, b: 1.2, phase: 3 },
        { l: 0.0046, a: 12, s: 0.0016, b: 3.5, phase: 4 },
      ],
      dashed: true,
      lineColor: (i) => `rgba(121, 210, 190, ${0.075 + i * 0.018})`,
      lineWidth: (i) => 1.4 + i * 0.25,
      shadowBlur: 10,
      shadowColor: "rgba(90, 190, 170, 0.28)",
      particleColor: (a) => `rgba(208, 237, 221, ${a})`,
    },
  };

  let linesMode = body.dataset.lines === "smt" ? "smt" : "classic";
  let preset = WAVE_PRESETS[linesMode];
  let particles = [];
  let tick = 0;
  let raf;

  function buildParticles() {
    if (linesMode === "classic") {
      particles = Array.from({ length: 80 }, () => ({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        sz: Math.random() * 2 + 0.4,
        vx: (Math.random() - 0.5) * 0.06,
        vy: -(Math.random() * 0.12 + 0.02),
        a: Math.random() * 0.35 + 0.08,
      }));
    } else {
      particles = Array.from({ length: 80 }, () => ({
        x: Math.random() * canvas.width,
        lane: Math.floor(Math.random() * preset.waves.length),
        sz: Math.random() * 1.8 + 0.8,
        vx: Math.random() * 0.18 + 0.08,
        a: Math.random() * 0.26 + 0.09,
      }));
    }
  }
  buildParticles();

  // Llamada desde el selector de tema para cambiar de lenguaje en caliente.
  function setLinesMode(next) {
    if (next !== "classic" && next !== "smt") return;
    linesMode = next;
    preset = WAVE_PRESETS[linesMode];
    buildParticles();
  }

  function draw() {
    raf = requestAnimationFrame(draw);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    tick += 0.6;
    const cy = canvas.height * 0.52;
    const laneGap = Math.min(62, canvas.height * 0.095);

    const laneY = (w, lane, x) =>
      cy +
      (lane - (preset.waves.length - 1) / 2) * laneGap +
      Math.sin(x * w.l + tick * w.s + w.b) * w.a +
      Math.sin(x * 0.0018 - tick * 0.0008 + w.phase) * 5;

    const classicY = (w, x) =>
      cy +
      Math.sin(x * w.l + tick * w.s + w.b) * w.a +
      Math.sin(x * 0.002 - tick * 0.0008 + w.phase) * 28 +
      Math.cos(x * 0.0008 + tick * 0.0005) * 18;

    preset.waves.forEach((w, i) => {
      ctx.beginPath();
      ctx.strokeStyle = preset.lineColor(i);
      ctx.lineWidth = preset.lineWidth(i);
      if (preset.dashed) {
        ctx.setLineDash([18, 12]);
        ctx.lineDashOffset = -tick * (0.42 + i * 0.05);
      } else {
        ctx.setLineDash([]);
      }
      ctx.shadowBlur = preset.shadowBlur;
      ctx.shadowColor = preset.shadowColor;
      for (let x = 0; x < canvas.width; x++) {
        const y = linesMode === "smt" ? laneY(w, i, x) : classicY(w, x);
        x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.stroke();
    });

    ctx.shadowBlur = 0;
    ctx.setLineDash([]);
    particles.forEach((p) => {
      if (linesMode === "classic") {
        ctx.beginPath();
        ctx.fillStyle = preset.particleColor(p.a);
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
      } else {
        const w = preset.waves[p.lane];
        const y = laneY(w, p.lane, p.x);
        ctx.fillStyle = preset.particleColor(p.a);
        ctx.fillRect(p.x, y - p.sz / 2, p.sz * 2.2, p.sz);
        p.x += p.vx;
        if (p.x > canvas.width + 12) {
          p.x = -12;
          p.lane = Math.floor(Math.random() * preset.waves.length);
        }
      }
    });
  }
  if (body.dataset.style !== "plano") draw();

  document.addEventListener("visibilitychange", () => {
    if (body.dataset.style === "plano") return;
    if (document.hidden) cancelAnimationFrame(raf);
    else draw();
  });

  // ---------- Selector de tema: tuerca en la esquina ----------
  // Persiste la preferencia en localStorage y la reaplica en cada carga
  // (la carga inicial ya se aplicó arriba, antes del primer paint).
  function applyBg(value) {
    body.dataset.bg = value === "smt" ? "smt" : "blue";
  }
  function applyLines(value) {
    const next = value === "smt" ? "smt" : "classic";
    body.dataset.lines = next;
    setLinesMode(next);
  }
  // Cambia entre "Atmosférico" y "Plano" en caliente, sin recargar.
  function applyStyleLive(value) {
    const next = value === "plano" ? "plano" : "atmosferico";
    const prev = body.dataset.style;
    body.dataset.style = next;
    if (next === "plano") {
      cancelAnimationFrame(raf);
    } else if (prev === "plano") {
      body.classList.add("awake", "logo-out", "hint-out");
      phase = "login";
      loginBox.style.display = "block";
      requestAnimationFrame(() =>
        requestAnimationFrame(() => {
          loginBox.classList.add("visible");
          if (authLayout) authLayout.classList.add("visible");
        })
      );
      draw();
    }
  }

  const themeFab = document.getElementById("theme-fab");
  const themePanel = document.getElementById("theme-panel");
  const colorInput = document.getElementById("theme-color-input");
  const colorReset = document.getElementById("theme-color-reset");

  if (colorInput && savedColor) colorInput.value = savedColor;

  if (themeFab && themePanel) {
    function setPanelOpen(open) {
      themePanel.classList.toggle("open", open);
      themeFab.setAttribute("aria-expanded", open ? "true" : "false");
      themePanel.setAttribute("aria-hidden", open ? "false" : "true");
    }

    function syncActiveButtons() {
      const hasCustomColor = !!body.style.getPropertyValue("--accent");
      themePanel.querySelectorAll("[data-group]").forEach((group) => {
        const key = group.dataset.group;
        const current =
          key === "lines" ? body.dataset.lines :
          key === "style" ? (body.dataset.style || "atmosferico") :
          key === "boot" ? (body.dataset.boot || "on") :
          body.dataset.bg;
        group.querySelectorAll("button").forEach((btn) => {
          const active = key === "bg" ? btn.dataset.value === current && !hasCustomColor
                                        : btn.dataset.value === current;
          btn.classList.toggle("is-active", active);
        });
      });
    }
    syncActiveButtons();

    themeFab.addEventListener("click", (e) => {
      e.stopPropagation();
      setPanelOpen(!themePanel.classList.contains("open"));
    });
    themePanel.addEventListener("click", (e) => e.stopPropagation());
    document.addEventListener("click", () => setPanelOpen(false));
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") setPanelOpen(false);
    });

    themePanel.querySelectorAll("button[data-value]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const group = btn.closest("[data-group]").dataset.group;
        if (group === "lines") {
          applyLines(btn.dataset.value);
          try { localStorage.setItem(STORAGE_KEY_LINES, btn.dataset.value); } catch (e) {}
        } else if (group === "bg") {
          applyColorVars(null); // un preset quita el color personalizado
          applyBg(btn.dataset.value);
          if (colorInput) colorInput.value = btn.dataset.value === "smt" ? "#164653" : "#1a3a8c";
          try {
            localStorage.setItem(STORAGE_KEY_BG, btn.dataset.value);
            localStorage.removeItem(STORAGE_KEY_COLOR);
          } catch (e) {}
        } else if (group === "style") {
          applyStyleLive(btn.dataset.value);
          try { localStorage.setItem(STORAGE_KEY_STYLE, btn.dataset.value); } catch (e) {}
        } else if (group === "boot") {
          body.dataset.boot = btn.dataset.value;
          // Si la intro está corriendo AHORA y la apagan, salta al login
          // de una vez en lugar de esperar a la siguiente carga.
          if (btn.dataset.value === "off" && typeof phase !== "undefined" && phase === "boot") {
            showLogin();
          }
          try { localStorage.setItem(STORAGE_KEY_BOOT, btn.dataset.value); } catch (e) {}
        }
        syncActiveButtons();
      });
    });

    if (colorInput) {
      colorInput.addEventListener("input", () => {
        applyColorVars(colorInput.value);
        try { localStorage.setItem(STORAGE_KEY_COLOR, colorInput.value); } catch (e) {}
        syncActiveButtons();
      });
    }
    if (colorReset) {
      colorReset.addEventListener("click", () => {
        applyColorVars(null);
        try { localStorage.removeItem(STORAGE_KEY_COLOR); } catch (e) {}
        syncActiveButtons();
      });
    }
  }

  // ---------- Secuencia de encendido (boot) ----------
  const loginBox = document.getElementById("login-box");
  const authLayout = document.querySelector(".auth-layout");
  let phase = "boot";
  let seq = [];

  // Si venimos con errores/avisos o directo al registro, saltamos la intro.
  const hasMessages = !!document.querySelector(".auth-messages");
  const wantsRegistro = body.dataset.tab === "registro";
  const isPlano = body.dataset.style === "plano";
  const bootDisabled = body.dataset.boot === "off";
  const skipIntro = hasMessages || wantsRegistro || isPlano || bootDisabled;

  function revealBox() {
    loginBox.style.display = "block";
    requestAnimationFrame(() =>
      requestAnimationFrame(() => {
        loginBox.classList.add("visible");
        if (authLayout) authLayout.classList.add("visible");
      })
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