document.addEventListener('DOMContentLoaded', () => {
    const botonesResolver = document.querySelectorAll('.resolver-btn');

    botonesResolver.forEach(boton => {
        boton.addEventListener('click', async (e) => {
            const idReporte = e.currentTarget.getAttribute('data-id');

            if (!confirm('¿Estás seguro de marcar esta incidencia como resuelta?')) {
                return;
            }

            try {
                const response = await fetch(`/admin/eliminar/${idReporte}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const data = await response.json();

                if (data.status === 'success') {
                    // Mostrar popup animado profesional
                    const popup = document.getElementById('successPopup');
                    if (popup) {
                        popup.style.display = 'block';
                        popup.style.animation = 'fadeInUp 0.4s ease-out forwards';
                        
                        setTimeout(() => {
                            popup.style.opacity = '0';
                            popup.style.transition = 'opacity 0.4s ease';
                            setTimeout(() => {
                                popup.style.display = 'none';
                                popup.style.opacity = '1';
                            }, 400);
                        }, 3000);
                    }

                    // Eliminar visualmente la fila de la tabla sin recargar la página
                    const fila = e.currentTarget.closest('tr');
                    fila.style.transition = 'all 0.4s ease';
                    fila.style.transform = 'scale(0.95)';
                    fila.style.opacity = '0';
                    
                    setTimeout(() => {
                        fila.remove();
                        const tbody = document.getElementById('tabla-admin-body');
                        if (tbody && tbody.children.length === 0) {
                            tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">No hay incidencias registradas en este momento.</td></tr>`;
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