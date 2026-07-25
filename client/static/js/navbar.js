/* ==========================================================================
   Menú de usuario + modal de "Configuración de cuenta".
   Nombre, correo, teléfono y foto se guardan de verdad contra el api/
   (PATCH a v1/trabajadores/<numeroNomina>/, via el endpoint
   usuarios:perfil_actualizar del client). La apariencia (tema/colores)
   sigue siendo solo local, ver theme.js. El botón de "Cerrar sesión" usa
   la vista de logout de Django.
   ========================================================================== */
(function () {
  const root = document.getElementById("userMenu");
  if (!root) return; // no hay sesión iniciada, nada que montar

  const username = root.dataset.username || "invitado";
  const perfilUrl = root.dataset.perfilUrl;

  function getCookie(nombre) {
    let valor = null;
    if (document.cookie && document.cookie !== "") {
      document.cookie.split(";").forEach((c) => {
        c = c.trim();
        if (c.substring(0, nombre.length + 1) === nombre + "=") {
          valor = decodeURIComponent(c.substring(nombre.length + 1));
        }
      });
    }
    return valor;
  }

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

  function iniciales(texto) {
    return (texto || "?").trim().charAt(0).toUpperCase();
  }

function pintarAvatar(fotoUrl, nombreParaInicial) {
  // Si no hay foto, directo a mostrar la inicial (sin intentar cargar nada).
  if (!fotoUrl) {
    avatarNodes.forEach((node) => {
      node.style.backgroundImage = "";
      node.textContent = iniciales(nombreParaInicial);
    });
    return;
  }

  // Mientras se confirma si la imagen carga, dejamos la inicial puesta
  // (evita el círculo vacío si la imagen tarda o nunca llega).
  avatarNodes.forEach((node) => {
    node.style.backgroundImage = "";
    node.textContent = iniciales(nombreParaInicial);
  });

  // Precarga: solo si la imagen realmente existe/carga se pone de fondo.
  // Si el fotoUrl es un data: URL (preview local del <input type=file>)
  // esto también funciona igual, siempre "carga" porque ya está en memoria.
  const probe = new Image();
  probe.onload = () => {
    avatarNodes.forEach((node) => {
      node.style.backgroundImage = `url(${fotoUrl})`;
      node.textContent = "";
    });
  };
  probe.onerror = () => {
    // 404 o cualquier error: se queda con la inicial, ya puesta arriba.
  };
  probe.src = fotoUrl;
}
  function pintarNombre(nombre, usuarioTxt) {
    document.querySelectorAll("[data-display-nombre]").forEach((n) => (n.textContent = nombre));
    document.querySelectorAll("[data-display-usuario]").forEach((n) => (n.textContent = `@${usuarioTxt}`));
  }

  /* ---------- carga inicial: viene directo de la sesión (ya real, del api/) ---------- */
  const nombreInicial = root.dataset.nombre || root.dataset.username;
  let nombreActual = nombreInicial; // se actualiza cada vez que se guarda un cambio de nombre
  let fotoGuardada = root.dataset.foto || null;
  pintarAvatar(fotoGuardada, nombreActual);

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

    // Se cierra sin guardar: se descarta cualquier foto/campo que haya
    // quedado a medias (si no, al reabrir se veria un preview que en
    // realidad nunca se mando al api/).
    archivoFotoPendiente = null;
    quitarFotoPendiente = false;
    if (avatarInput) avatarInput.value = "";
    pintarAvatar(fotoGuardada, nombreActual);
    if (form) form.reset();
  }

  if (openConfigBtn) openConfigBtn.addEventListener("click", abrirModal);
  if (modalClose) modalClose.addEventListener("click", cerrarModal);
  if (modalCancel) modalCancel.addEventListener("click", cerrarModal);
  if (modalBackdrop) modalBackdrop.addEventListener("click", cerrarModal);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modal && modal.classList.contains("is-open")) cerrarModal();
  });

  /* ---------- foto de perfil ----------
     No se manda nada al api/ hasta que se le da "Guardar cambios": aqui solo
     se guarda el archivo elegido (o la intención de quitar la foto) y se
     pinta el preview. */
  let archivoFotoPendiente = null; // File elegido en avatarInput, o null
  let quitarFotoPendiente = false; // true si dieron "Quitar foto"

  function previsualizarArchivo(file) {
    const reader = new FileReader();
    reader.onload = () => pintarAvatar(reader.result, form ? form.nombre.value : nombreInicial);
    reader.readAsDataURL(file);
  }

  if (avatarInput) {
    avatarInput.addEventListener("change", () => {
      const file = avatarInput.files && avatarInput.files[0];
      if (!file) return;
      if (!file.type.startsWith("image/")) return;

      archivoFotoPendiente = file;
      quitarFotoPendiente = false;
      previsualizarArchivo(file);
    });
  }

  if (avatarRemoveBtn) {
    avatarRemoveBtn.addEventListener("click", () => {
      archivoFotoPendiente = null;
      quitarFotoPendiente = true;
      if (avatarInput) avatarInput.value = "";
      pintarAvatar(null, form ? form.nombre.value : nombreInicial);
    });
  }

  /* ---------- guardar cambios: PATCH real contra el api/ ---------- */
  function mostrarToast(msg, esError) {
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.toggle("is-error", !!esError);
    toast.classList.add("is-visible");
    window.clearTimeout(mostrarToast._t);
    mostrarToast._t = window.setTimeout(() => toast.classList.remove("is-visible"), 2600);
  }

  function primerError(errores) {
    if (!errores || typeof errores !== "object") return "No se pudieron guardar los cambios.";
    const primeraClave = Object.keys(errores)[0];
    if (!primeraClave) return "No se pudieron guardar los cambios.";
    const detalle = errores[primeraClave];
    return Array.isArray(detalle) ? detalle[0] : String(detalle);
  }

  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      if (!perfilUrl) return;

      const nombre = form.nombre.value.trim() || nombreInicial;
      const submitBtn = form.querySelector('button[type="submit"]');

      const datos = new FormData();
      datos.append("nombre", nombre);
      datos.append("correo", form.correo.value.trim());
      datos.append("telefono", form.telefono.value.trim());
      if (archivoFotoPendiente) {
        datos.append("foto", archivoFotoPendiente);
      } else if (quitarFotoPendiente) {
        datos.append("eliminar_foto", "1");
      }

      if (submitBtn) submitBtn.disabled = true;

      fetch(perfilUrl, {
        method: "POST",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
        body: datos,
      })
        .then((r) => r.json().then((data) => ({ ok: r.ok, data })))
        .then(({ ok, data }) => {
          if (!ok || !data.ok) {
            mostrarToast(primerError(data.errores), true);
            return;
          }

          const usuario = data.usuario || {};
          fotoGuardada = usuario.foto || null;
          nombreActual = usuario.nombre || nombre;
          archivoFotoPendiente = null;
          quitarFotoPendiente = false;

          form.nombre.defaultValue = form.nombre.value;
          form.correo.defaultValue = form.correo.value;
          form.telefono.defaultValue = form.telefono.value;

          pintarNombre(nombreActual, username);
          pintarAvatar(fotoGuardada, nombreActual);

          cerrarModal();
          mostrarToast("Cambios guardados.");
        })
        .catch(() => mostrarToast("No se pudo conectar con el servidor.", true))
        .finally(() => {
          if (submitBtn) submitBtn.disabled = false;
        });
    });
  }
})();
