/* ==========================================================================
   Menú de usuario + modal de "Configuración de cuenta".
   La edición de datos y la foto son PROTOTIPO: se guardan solo en
   localStorage (por usuario) para poder demostrar el flujo sin tener
   todavía un endpoint en el api/ para actualizarlos. El botón de
   "Cerrar sesión" sí es real y usa la vista de logout de Django.
   ========================================================================== */
(function () {
  const root = document.getElementById("userMenu");
  if (!root) return; // no hay sesión iniciada, nada que montar

  const username = root.dataset.username || "invitado";
  const storageKey = `operacore_perfil_${username}`;

  const trigger = document.getElementById("userMenuTrigger");
  const dropdown = document.getElementById("userMenuDropdown");
  const openConfigBtn = document.getElementById("openConfigBtn");

  const modal = document.getElementById("configModal");
  const modalClose = document.getElementById("configModalClose");
  const modalCancel = document.getElementById("configModalCancel");
  const modalBackdrop = modal ? modal.querySelector(".config-modal__backdrop") : null;
  const form = document.getElementById("configForm");

  const avatarInput = document.getElementById("avatarInput");
  const avatarRemoveBtn = document.getElementById("avatarRemoveBtn");
  const avatarNodes = document.querySelectorAll("[data-avatar-node]");

  const toast = document.getElementById("configToast");

  /* ---------- estado guardado (prototipo, por navegador) ---------- */
  function leerPerfilGuardado() {
    try {
      const raw = localStorage.getItem(storageKey);
      return raw ? JSON.parse(raw) : {};
    } catch (e) {
      return {};
    }
  }

  function guardarPerfil(data) {
    try {
      localStorage.setItem(storageKey, JSON.stringify(data));
    } catch (e) {
      /* localStorage puede fallar en modo privado; no es crítico para el prototipo */
    }
  }

  function iniciales(texto) {
    return (texto || "?").trim().charAt(0).toUpperCase();
  }

  function pintarAvatar(fotoDataUrl, nombreParaInicial) {
    avatarNodes.forEach((node) => {
      if (fotoDataUrl) {
        node.style.backgroundImage = `url(${fotoDataUrl})`;
        node.textContent = "";
      } else {
        node.style.backgroundImage = "";
        node.textContent = iniciales(nombreParaInicial);
      }
    });
  }

  function pintarNombre(nombre, usuarioTxt) {
    document.querySelectorAll("[data-display-nombre]").forEach((n) => (n.textContent = nombre));
    document.querySelectorAll("[data-display-usuario]").forEach((n) => (n.textContent = `@${usuarioTxt}`));
  }

  /* ---------- carga inicial: combina lo del servidor con lo guardado local ---------- */
  const perfilGuardado = leerPerfilGuardado();
  const nombreInicial = perfilGuardado.nombre || root.dataset.nombre || root.dataset.username;
  pintarAvatar(perfilGuardado.foto || null, nombreInicial);
  if (perfilGuardado.nombre) pintarNombre(perfilGuardado.nombre, perfilGuardado.usuario || username);

  if (form) {
    if (perfilGuardado.nombre) form.nombre.value = perfilGuardado.nombre;
    if (perfilGuardado.correo) form.correo.value = perfilGuardado.correo;
    if (perfilGuardado.telefono) form.telefono.value = perfilGuardado.telefono;
  }

  /* ---------- dropdown ---------- */
  function cerrarDropdown() {
    dropdown.classList.remove("is-open");
    trigger.setAttribute("aria-expanded", "false");
  }
  function abrirDropdown() {
    dropdown.classList.add("is-open");
    trigger.setAttribute("aria-expanded", "true");
  }

  trigger.addEventListener("click", (e) => {
    e.stopPropagation();
    dropdown.classList.contains("is-open") ? cerrarDropdown() : abrirDropdown();
  });

  document.addEventListener("click", (e) => {
    if (!root.contains(e.target)) cerrarDropdown();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") cerrarDropdown();
  });

  /* ---------- modal de configuración ---------- */
  function abrirModal() {
    cerrarDropdown();
    if (!modal) return;
    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
  }
  function cerrarModal() {
    if (!modal) return;
    modal.classList.remove("is-open");
    modal.setAttribute("aria-hidden", "true");
  }

  if (openConfigBtn) openConfigBtn.addEventListener("click", abrirModal);
  if (modalClose) modalClose.addEventListener("click", cerrarModal);
  if (modalCancel) modalCancel.addEventListener("click", cerrarModal);
  if (modalBackdrop) modalBackdrop.addEventListener("click", cerrarModal);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modal && modal.classList.contains("is-open")) cerrarModal();
  });

  /* ---------- foto de perfil (prototipo, se guarda como base64 local) ---------- */
  let fotoActual = perfilGuardado.foto || null;

  if (avatarInput) {
    avatarInput.addEventListener("change", () => {
      const file = avatarInput.files && avatarInput.files[0];
      if (!file) return;
      if (!file.type.startsWith("image/")) return;

      const reader = new FileReader();
      reader.onload = () => {
        fotoActual = reader.result;
        pintarAvatar(fotoActual, form ? form.nombre.value : nombreInicial);
      };
      reader.readAsDataURL(file);
    });
  }

  if (avatarRemoveBtn) {
    avatarRemoveBtn.addEventListener("click", () => {
      fotoActual = null;
      if (avatarInput) avatarInput.value = "";
      pintarAvatar(null, form ? form.nombre.value : nombreInicial);
    });
  }

  /* ---------- guardar cambios (prototipo: no pega al api/, solo local) ---------- */
  function mostrarToast(msg) {
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add("is-visible");
    window.clearTimeout(mostrarToast._t);
    mostrarToast._t = window.setTimeout(() => toast.classList.remove("is-visible"), 2600);
  }

  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const nombre = form.nombre.value.trim() || nombreInicial;
      const correo = form.correo.value.trim();
      const telefono = form.telefono.value.trim();

      const nuevoPerfil = { nombre, correo, telefono, usuario: username, foto: fotoActual };
      guardarPerfil(nuevoPerfil);

      pintarNombre(nombre, username);
      pintarAvatar(fotoActual, nombre);

      cerrarModal();
      mostrarToast("Cambios guardados en este navegador (modo prototipo).");
    });
  }
})();
