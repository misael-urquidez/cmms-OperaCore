document.addEventListener('DOMContentLoaded', () => {
    const btnAbrir = document.getElementById('btnAbrirModalBaja');
    const btnCancelar = document.getElementById('btnCancelarBaja');
    const modal = document.getElementById('modalBaja');

    if (!btnAbrir || !modal) return;

    // Función para abrir modal
    const abrirModal = () => {
        modal.classList.add('active');
    };

    // Función para cerrar modal
    const cerrarModal = () => {
        modal.classList.remove('active');
    };

    // Eventos
    btnAbrir.addEventListener('click', abrirModal);

    if (btnCancelar) {
        btnCancelar.addEventListener('click', cerrarModal);
    }

    // Cerrar al hacer click fuera de la ventana modal
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            cerrarModal();
        }
    });

    // Cerrar modal con la tecla Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            cerrarModal();
        }
    });
});