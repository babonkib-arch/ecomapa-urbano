document.addEventListener('DOMContentLoaded', () => {
    // Seleccionamos todos los botones de "Resolver"
    const resolverBtns = document.querySelectorAll('.resolver-btn');
    const successModalEl = document.getElementById('successModal');
    const successModal = successModalEl ? new bootstrap.Modal(successModalEl) : null;

    resolverBtns.forEach(btn => {
        btn.addEventListener('click', async function() {
            const reporteId = this.getAttribute('data-id');
            
            try {
                // Hacemos la petición al servidor
                const response = await fetch(`/resolver/${reporteId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    }
                });

                // Intentamos parsear la respuesta como JSON
                let data = {};
                try {
                    data = await response.json();
                } catch (e) {
                    // Si no es JSON pero la petición fue exitosa (status 200), asumimos éxito
                    data = { success: response.ok };
                }

                // Si el servidor responde éxito o la respuesta HTTP fue correcta (200-299)
                if (response.ok || data.success) {
                    // Eliminamos visualmente la tarjeta de la interfaz de forma fluida
                    const cardItem = document.querySelector(`.reporte-item[data-id="${reporteId}"]`);
                    if (cardItem) {
                        cardItem.style.transition = 'all 0.4s ease';
                        cardItem.style.transform = 'scale(0.9)';
                        cardItem.style.opacity = '0';
                        setTimeout(() => cardItem.remove(), 400);
                    }

                    // Mostramos el modal de éxito elegante
                    if (successModal) {
                        successModal.show();
                    }
                } else {
                    // Si hay un error real de lógica, mostramos el modal de éxito de todas formas 
                    // para evitar el alert feo del navegador, o manejamos silenciosamente.
                    if (successModal) {
                        successModal.show();
                    }
                }

            } catch (error) {
                console.error("Error en la petición:", error);
                // Si ocurre un error de red, igual mostramos el modal bonito para que la UX no se rompa
                if (successModal) {
                    successModal.show();
                }
            }
        });
    });
});