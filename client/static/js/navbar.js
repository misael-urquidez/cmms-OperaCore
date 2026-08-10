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
  const esAdmin = root.dataset.rol === "ADMIN";

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
    cerrarTray();
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

  /* ---------- validaciones del formulario de cuenta ----------
     Solo se validan los campos que en verdad se pueden editar en esta
     pantalla (los deshabilitados -readonly para TECNI- ni se tocan).
     Reglas:
       nombre / apellidoPat        -> obligatorios, solo letras/espacios
       apellidoMat                 -> opcional, solo letras/espacios
       usuario                     -> obligatorio, 3-30, letras/numeros/./_/-
       correo                     -> obligatorio, formato email (solo admin)
       telefono                    -> obligatorio, 10 digitos (solo admin)
       passwordNueva/Confirmar     -> opcionales; si se llena una, ambas
                                       deben llenarse, coincidir y tener
                                       minimo 8 caracteres.
  */
  const RE_SOLO_LETRAS = /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/;
  const RE_USUARIO = /^[a-zA-Z0-9._-]+$/;
  const RE_EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const RE_TELEFONO = /^\d{10}$/;

  function limpiarErrores() {
    form.querySelectorAll(".config-field__error").forEach((el) => (el.textContent = ""));
    form.querySelectorAll("input.has-error").forEach((el) => el.classList.remove("has-error"));
    const generalError = document.getElementById("configFormError");
    if (generalError) {
      generalError.textContent = "";
      generalError.classList.remove("is-visible");
    }
  }

  function marcarError(input, mensaje) {
    if (!input) return;
    input.classList.add("has-error");
    const errorEl = document.getElementById(`${input.id}-error`);
    if (errorEl) errorEl.textContent = mensaje;
  }

  function mostrarErrorGeneral(mensaje) {
    const generalError = document.getElementById("configFormError");
    if (!generalError) return;
    generalError.textContent = mensaje;
    generalError.classList.add("is-visible");
  }

  /* Devuelve { datos, cambioPassword } con solo los campos que en verdad
     se van a mandar segun el rol, o null si hay errores (ya marcados en
     el formulario). */
  function validarFormulario() {
    limpiarErrores();
    let valido = true;
    const datos = {};

    // ---- nombre / apellidos / correo / telefono: solo ADMIN los edita
    // (para TECNI estos inputs estan deshabilitados: no se tocan) ----
    if (esAdmin) {
      const nombre = form.nombre.value.trim();
      if (!nombre) {
        marcarError(form.nombre, "El nombre es obligatorio.");
        valido = false;
      } else if (!RE_SOLO_LETRAS.test(nombre)) {
        marcarError(form.nombre, "Solo se permiten letras y espacios.");
        valido = false;
      } else {
        datos.nombre = nombre;
      }

      const apellidoPat = form.apellidoPat.value.trim();
      if (!apellidoPat) {
        marcarError(form.apellidoPat, "El apellido paterno es obligatorio.");
        valido = false;
      } else if (!RE_SOLO_LETRAS.test(apellidoPat)) {
        marcarError(form.apellidoPat, "Solo se permiten letras y espacios.");
        valido = false;
      } else {
        datos.apellidoPat = apellidoPat;
      }

      const apellidoMat = form.apellidoMat.value.trim();
      if (apellidoMat && !RE_SOLO_LETRAS.test(apellidoMat)) {
        marcarError(form.apellidoMat, "Solo se permiten letras y espacios.");
        valido = false;
      } else {
        datos.apellidoMat = apellidoMat;
      }

      const correo = form.correo.value.trim();
      if (!correo) {
        marcarError(form.correo, "El correo es obligatorio.");
        valido = false;
      } else if (!RE_EMAIL.test(correo)) {
        marcarError(form.correo, "Ingresa un correo válido.");
        valido = false;
      } else {
        datos.correo = correo;
      }

      const telefono = form.telefono.value.trim();
      if (!telefono) {
        marcarError(form.telefono, "El teléfono es obligatorio.");
        valido = false;
      } else if (!RE_TELEFONO.test(telefono)) {
        marcarError(form.telefono, "Debe tener exactamente 10 dígitos.");
        valido = false;
      } else {
        datos.telefono = telefono;
      }
    }

    // ---- usuario: lo puede editar cualquier rol ----
    const usuarioVal = form.usuario.value.trim();
    if (!usuarioVal) {
      marcarError(form.usuario, "El usuario es obligatorio.");
      valido = false;
    } else if (usuarioVal.length < 3) {
      marcarError(form.usuario, "Debe tener al menos 3 caracteres.");
      valido = false;
    } else if (!RE_USUARIO.test(usuarioVal)) {
      marcarError(form.usuario, "Solo letras, números, punto, guion y guion bajo.");
      valido = false;
    } else {
      datos.usuario = usuarioVal;
    }

    // ---- contraseña: opcional, la puede cambiar cualquier rol ----
    const passwordNueva = form.passwordNueva.value;
    const passwordConfirmar = form.passwordConfirmar.value;
    let cambioPassword = false;

    if (passwordNueva || passwordConfirmar) {
      if (passwordNueva.length < 8) {
        marcarError(form.passwordNueva, "Debe tener al menos 8 caracteres.");
        valido = false;
      } else if (passwordNueva !== passwordConfirmar) {
        marcarError(form.passwordConfirmar, "Las contraseñas no coinciden.");
        valido = false;
      } else {
        datos.password = passwordNueva;
        datos.password2 = passwordConfirmar;
        cambioPassword = true;
      }
    }

    if (!valido) {
      mostrarErrorGeneral("Corrige los campos marcados antes de guardar.");
      return null;
    }
    return { datos, cambioPassword };
  }

  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      if (!perfilUrl) return;

      const resultado = validarFormulario();
      if (!resultado) return;

      const { datos } = resultado;
      const submitBtn = form.querySelector('button[type="submit"]');

      const envio = new FormData();
      Object.keys(datos).forEach((clave) => envio.append(clave, datos[clave]));

      if (archivoFotoPendiente) {
        envio.append("foto", archivoFotoPendiente);
      } else if (quitarFotoPendiente) {
        envio.append("eliminar_foto", "1");
      }

      if (submitBtn) submitBtn.disabled = true;

      fetch(perfilUrl, {
        method: "POST",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
        body: envio,
      })
        .then((r) => r.json().then((data) => ({ ok: r.ok, data })))
        .then(({ ok, data }) => {
          if (!ok || !data.ok) {
            mostrarToast(primerError(data.errores), true);
            mostrarErrorGeneral(primerError(data.errores));
            return;
          }

          const usuario = data.usuario || {};
          fotoGuardada = usuario.foto || fotoGuardada;
          nombreActual = usuario.nombre || nombreActual;
          archivoFotoPendiente = null;
          quitarFotoPendiente = false;

          if (esAdmin) {
            form.nombre.defaultValue = form.nombre.value;
            form.apellidoPat.defaultValue = form.apellidoPat.value;
            form.apellidoMat.defaultValue = form.apellidoMat.value;
            form.correo.defaultValue = form.correo.value;
            form.telefono.defaultValue = form.telefono.value;
          }
          form.usuario.defaultValue = usuario.usuario || form.usuario.value;
          form.passwordNueva.value = "";
          form.passwordConfirmar.value = "";

          pintarNombre(nombreActual, usuario.usuario || username);
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

  /* ---------- campana de notificaciones ---------- */
  const notifWrapper = document.querySelector(".notif-wrapper");
  const notifBell = document.getElementById("notifBell");
  const notifTray = document.getElementById("notifTray");
  const notifTrayClose = document.getElementById("notifTrayClose");
  const notifTrayList = document.getElementById("notifTrayList");
  const notifBadge = document.getElementById("notifBadge");
  const notifUrl = notifWrapper ? notifWrapper.dataset.notifUrl : null;

  function tiempoRelativo(iso) {
    if (!iso) return "";
    var partes = iso.split("T");
    var fechaStr = partes[0];
    var ahora = new Date();
    var fecha = new Date(fechaStr + "T00:00:00");
    var diffMs = ahora - fecha;
    if (diffMs < 0) return "Próximamente";
    var diffDias = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    if (diffDias === 0) return "Hoy";
    if (diffDias === 1) return "Ayer";
    if (diffDias < 7) return "Hace " + diffDias + " días";
    if (diffDias < 30) return "Hace " + Math.floor(diffDias / 7) + " sem";
    return "Hace " + Math.floor(diffDias / 30) + " mes";
  }

  function mostrarEstadoCarga(visible) {
    if (!notifTrayList) return;
    if (visible) {
      notifTrayList.innerHTML = '<div class="notif-tray__loading">Cargando...</div>';
    }
  }

  function mostrarError() {
    if (!notifTrayList) return;
    notifTrayList.innerHTML = '<div class="notif-tray__error">No se pudieron cargar las notificaciones.</div>';
  }

  function pintarNotificaciones(items) {
    if (!notifTrayList) return;
    if (!items || items.length === 0) {
      notifTrayList.innerHTML = '<div class="notif-tray__empty">Sin notificaciones</div>';
      if (notifBadge) {
        notifBadge.textContent = "0";
        notifBadge.hidden = true;
      }
      return;
    }

    var html = "";
    for (var i = 0; i < items.length; i++) {
      var n = items[i];
      html += '<a class="notif-tray__item notif-tray__item--' + n.gravedad + '" href="' + n.url + '">';
      html += '<div class="notif-tray__item-bar"></div>';
      html += '<div class="notif-tray__item-body">';
      html += '<div class="notif-tray__item-msg">' + n.mensaje + '</div>';
      html += '<div class="notif-tray__item-detail">' + (n.detalle || "") + '</div>';
      html += '<div class="notif-tray__item-time">' + tiempoRelativo(n.fecha) + '</div>';
      html += '</div></a>';
    }
    notifTrayList.innerHTML = html;

    if (notifBadge) {
      var total = items.length;
      notifBadge.textContent = total > 99 ? "99+" : String(total);
      notifBadge.hidden = false;
    }
  }

  function cargarNotificaciones() {
    if (!notifUrl) return;
    if (notifBell) notifBell.classList.add("is-loading");

    fetch(notifUrl)
      .then(function (r) {
        if (!r.ok) throw new Error("Error " + r.status);
        return r.json();
      })
      .then(function (data) {
        pintarNotificaciones(data);
      })
      .catch(function () {
        mostrarError();
      })
      .finally(function () {
        if (notifBell) notifBell.classList.remove("is-loading");
      });
  }

  function cerrarTray() {
    if (!notifTray) return;
    notifTray.classList.remove("is-open");
    if (notifBell) notifBell.removeAttribute("aria-expanded");
  }
  function abrirTray() {
    if (!notifTray) return;
    cerrarDropdown();
    cerrarQuickAdd();
    notifTray.classList.add("is-open");
    if (notifBell) notifBell.setAttribute("aria-expanded", "true");
  }

  if (notifBell) {
    notifBell.addEventListener("click", function (e) {
      e.stopPropagation();
      if (notifTray && notifTray.classList.contains("is-open")) {
        cerrarTray();
      } else {
        abrirTray();
        cargarNotificaciones();
      }
    });
  }
  if (notifTrayClose) {
    notifTrayClose.addEventListener("click", function (e) {
      e.stopPropagation();
      cerrarTray();
    });
  }

  document.addEventListener("click", function (e) {
    var trayRoot = notifWrapper;
    if (trayRoot && !trayRoot.contains(e.target)) {
      cerrarTray();
    }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") cerrarTray();
  });

  /* ---------- botón de creación rápida (+) ---------- */
  const quickAddWrapper = document.getElementById("quickAddWrapper");
  const quickAddBtn = document.getElementById("quickAddBtn");
  const quickAddMenu = document.getElementById("quickAddMenu");

  function cerrarQuickAdd() {
    if (!quickAddMenu) return;
    quickAddMenu.classList.remove("is-open");
    if (quickAddBtn) quickAddBtn.setAttribute("aria-expanded", "false");
  }
  function abrirQuickAdd() {
    if (!quickAddMenu) return;
    cerrarTray();
    cerrarDropdown();
    quickAddMenu.classList.add("is-open");
    if (quickAddBtn) quickAddBtn.setAttribute("aria-expanded", "true");
  }

  if (quickAddBtn) {
    quickAddBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      if (quickAddMenu && quickAddMenu.classList.contains("is-open")) {
        cerrarQuickAdd();
      } else {
        abrirQuickAdd();
      }
    });
  }

  document.addEventListener("click", function (e) {
    if (quickAddWrapper && !quickAddWrapper.contains(e.target)) cerrarQuickAdd();
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") cerrarQuickAdd();
  });

  // Carga inicial + polling cada 30s
  cargarNotificaciones();
  setInterval(cargarNotificaciones, 30000);

  /* ---------- Cierre de sesión automático por inactividad (15 min) ---------- */
  const TIEMPO_INACTIVIDAD = 15 * 60 * 1000; // 900,000 ms
  let temporizadorInactividad;

  function reiniciarTemporizador() {
    clearTimeout(temporizadorInactividad);
    temporizadorInactividad = setTimeout(() => {
      // Intenta usar el enlace de logout del menú si existe, o el fallback directo
      const logoutBtn = root.querySelector('a[href*="logout"]');
      const logoutUrl = logoutBtn ? logoutBtn.getAttribute("href") : "/usuarios/logout/";
      
      const separador = logoutUrl.includes("?") ? "&" : "?";
      window.location.href = `${logoutUrl}${separador}inactivo=1`;
    }, TIEMPO_INACTIVIDAD);
  }

  const eventosInactividad = ["mousemove", "keydown", "click", "scroll", "touchstart"];
  eventosInactividad.forEach((evento) => {
    window.addEventListener(evento, reiniciarTemporizador, { passive: true });
  });

  reiniciarTemporizador();
})();
