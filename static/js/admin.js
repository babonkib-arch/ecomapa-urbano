document.addEventListener('DOMContentLoaded', () => {
    const botonesResolver = document.querySelectorAll('.resolver-btn');

    botonesResolver.forEach(boton => {
        boton.addEventListener('click', async (e) => {
            const btn = e.currentTarget;
            const idReporte = btn.getAttribute('data-id');
            const fila = btn.closest('tr');

            try {
                const response = await fetch(`/admin/eliminar/${idReporte}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const data = await response.json();

                if (data.status === 'success') {
                    // Mostrar modal visual idéntico al de registro de usuario
                    const successModalEl = document.getElementById('successModal');
                    const successModal = new bootstrap.Modal(successModalEl);
                    successModal.show();

                    // Animar y eliminar la fila de la tabla limpiamente
                    fila.style.transition = 'all 0.4s ease';
                    fila.style.transform = 'scale(0.95)';
                    fila.style.opacity = '0';
                    
                    setTimeout(() => {
                        fila.remove();
                        const tbody = document.getElementById('tabla-admin-body');
                        if (tbody && tbody.children.length === 0) {
                            tbody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-muted">No hay incidencias registradas en este momento.</td></tr>`;
                        }
                    }, 400);

                } else {
                    alert('Error: ' + (data.message || 'No se pudo completar la acción.'));
                }
            } catch (error) {
                console.error('Error en la petición:', error);
                alert('Hubo un error al procesar la solicitud.');
            }
        });
    });
});