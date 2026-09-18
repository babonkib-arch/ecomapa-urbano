// Control de Pantalla de Inicio y Transición Fluida
document.addEventListener('DOMContentLoaded', () => {
    const splash = document.getElementById('splash-screen');
    const btnEntrar = document.getElementById('btn-entrar');
    const mapContainer = document.getElementById('map-container');

    if (btnEntrar && splash && mapContainer) {
        btnEntrar.addEventListener('click', () => {
            splash.classList.add('splash-hidden');
            setTimeout(() => {
                mapContainer.classList.add('visible');
                map.invalidateSize(); 
            }, 400);
        });
    }
});

// Control visual del campo "Otro problema"
const selectCategoria = document.getElementById('select_categoria');
const divOtroProblema = document.getElementById('divOtroProblema');
const inputOtroProblema = document.getElementById('inputOtroProblema');

if (selectCategoria) {
    selectCategoria.addEventListener('change', function() {
        if (this.value === 'otro') {
            divOtroProblema.classList.remove('d-none');
            inputOtroProblema.required = true;
        } else {
            divOtroProblema.classList.add('d-none');
            inputOtroProblema.required = false;
        }
    });
}

// Inicialización del Mapa
const map = L.map('map').setView([-33.12, -58.30], 13);
const modalElement = document.getElementById('reporteModal') ? new bootstrap.Modal(document.getElementById('reporteModal')) : null;

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

// Marcadores Personalizados (Iconos Semáforo)
const redIcon = L.icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41]
});

const greenIcon = L.icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41]
});

let markersGroup = L.layerGroup().addTo(map);

// Carga de Puntos
function cargarReportes() {
    fetch('/api/reportes')
        .then(res => res.json())
        .then(data => {
            markersGroup.clearLayers();
            data.forEach(rep => {
                const icon = rep.estado === 'Resuelto' ? greenIcon : redIcon;
                const badgeColor = rep.estado === 'Resuelto' ? 'bg-success' : 'bg-danger';
                const imgHtml = rep.foto_path ? `<img src="${rep.foto_path}" class="img-fluid rounded-3 mt-2 shadow-sm" style="max-height:140px; width:100%; object-fit:cover;">` : '';
                
                // Texto y enlace para compartir
                const textoCompartir = encodeURIComponent(`¡Incidencia en EcoMapa Fray Bentos!\nCategoría: ${rep.categoria}\nEstado: ${rep.estado}\nDescripción: ${rep.descripcion}`);
                const urlActual = encodeURIComponent(window.location.href);

                L.marker([rep.latitud, rep.longitud], { icon: icon })
                    .bindPopup(`
                        <div style="max-width:270px;" class="p-1">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span class="badge ${badgeColor}">${rep.estado}</span>
                                <span class="badge bg-secondary">${rep.gravedad || 'Normal'}</span>
                            </div>
                            <h6 class="fw-bold mb-1 text-dark" style="font-size: 1rem;">${rep.categoria}</h6>
                            <p class="small text-muted mb-2" style="font-size: 0.85rem;">${rep.descripcion}</p>
                            ${imgHtml}
                            
                            <div class="mt-3 pt-2 border-top">
                                <div class="text-muted text-center fw-bold mb-2" style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px;">
                                    <i class="fa-solid fa-share-nodes me-1 text-success"></i> Compartir reporte:
                                </div>
                                <div class="d-flex justify-content-center gap-2">
                                    <!-- WhatsApp -->
                                    <a href="https://api.whatsapp.com/send?text=${textoCompartir}" target="_blank" title="Compartir en WhatsApp" 
                                       style="width: 35px; height: 35px; background: #25d366; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; text-decoration: none; font-size: 16px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                                        <i class="fa-brands fa-whatsapp"></i>
                                    </a>
                                    <!-- Facebook -->
                                    <a href="https://www.facebook.com/sharer/sharer.php?u=${urlActual}" target="_blank" title="Compartir en Facebook" 
                                       style="width: 35px; height: 35px; background: #1877f2; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; text-decoration: none; font-size: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                                        <i class="fa-brands fa-facebook-f"></i>
                                    </a>
                                    <!-- Twitter / X -->
                                    <a href="https://twitter.com/intent/tweet?text=${textoCompartir}&url=${urlActual}" target="_blank" title="Compartir en X" 
                                       style="width: 35px; height: 35px; background: #000000; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; text-decoration: none; font-size: 14px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                                        <i class="fa-brands fa-x-twitter"></i>
                                    </a>
                                    <!-- Telegram -->
                                    <a href="https://t.me/share/url?url=${urlActual}&text=${textoCompartir}" target="_blank" title="Compartir en Telegram" 
                                       style="width: 35px; height: 35px; background: #229ed9; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; text-decoration: none; font-size: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                                        <i class="fa-brands fa-telegram"></i>
                                    </a>
                                    <!-- Copiar Enlace -->
                                    <button onclick="navigator.clipboard.writeText(window.location.href); alert('¡Enlace copiado al portapapeles!');" title="Copiar Enlace" 
                                            style="width: 35px; height: 35px; background: #6c757d; color: white; border: none; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; cursor: pointer; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                                        <i class="fa-solid fa-link"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    `)
                    .addTo(markersGroup);
            });
        });
}

// Abrir Ventana Flotante al Hacer Clic en el Mapa
map.on('click', (e) => {
    document.getElementById('latitud').value = e.latlng.lat;
    document.getElementById('longitud').value = e.latlng.lng;
    if (selectCategoria) selectCategoria.value = "";
    if (divOtroProblema) divOtroProblema.classList.add('d-none');
    if (inputOtroProblema) inputOtroProblema.value = "";
    if (modalElement) modalElement.show();
});

// Envío del Formulario con Alerta SweetAlert2 y Tick Verde
const formReporte = document.getElementById('formReporte');
if (formReporte) {
    formReporte.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);

        if (selectCategoria && selectCategoria.value === 'otro') {
            const detallePersonalizado = inputOtroProblema.value;
            formData.set('id_categoria', 1);
            const descOriginal = document.getElementById('txtDescripcion').value;
            formData.set('descripcion', `[OTRO: ${detallePersonalizado}] ${descOriginal}`);
        }

        fetch('/api/reportes', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success' || (data.message && data.message.includes('exitosamente'))) {
                if (modalElement) modalElement.hide();
                this.reset();
                if (divOtroProblema) divOtroProblema.classList.add('d-none');
                cargarReportes();
                
                Swal.fire({
                    icon: 'success',
                    title: '¡Reporte Enviado!',
                    text: 'El incidente fue registrado exitosamente en el mapa.',
                    confirmButtonColor: '#198754',
                    customClass: { popup: 'rounded-4' }
                });
            } else {
                alert('Error al guardar reporte: ' + (data.message || 'Error desconocido'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Hubo un error al conectar con el servidor.');
        });
    });
}

cargarReportes();