document.addEventListener('DOMContentLoaded', () => {
    // Detectar elementos para modal de Baja o de Reactivación
    const btnAbrirBaja = document.getElementById('btnAbrirModalBaja');
    const btnCancelarBaja = document.getElementById('btnCancelarBaja');
    const modalBaja = document.getElementById('modalBaja');

    const btnAbrirReactivar = document.getElementById('btnAbrirModalReactivar');
    const btnCancelarReactivar = document.getElementById('btnCancelarReactivar');
    const modalReactivar = document.getElementById('modalReactivar');

    // Función genérica para vincular modal
    const setupModal = (btnAbrir, btnCancelar, modal) => {
        if (!btnAbrir || !modal) return;

        const abrir = () => modal.classList.add('active');
        const cerrar = () => modal.classList.remove('active');

        btnAbrir.addEventListener('click', abrir);
        if (btnCancelar) btnCancelar.addEventListener('click', cerrar);

        modal.addEventListener('click', (e) => {
            if (e.target === modal) cerrar();
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal.classList.contains('active')) cerrar();
        });
    };

    // Inicializar el modal que aplique
    setupModal(btnAbrirBaja, btnCancelarBaja, modalBaja);
    setupModal(btnAbrirReactivar, btnCancelarReactivar, modalReactivar);
});