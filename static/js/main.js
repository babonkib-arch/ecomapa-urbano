let map;
let activeMarker = null;
let reportesCache = [];

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    cargarReportesPublicos();
    setupImagePreview();

    const form = document.getElementById('form-reporte-mobile');
    if (form) {
        form.addEventListener('submit', enviarReporte);
    }
});

function initMap() {
    // Centrar por defecto en Fray Bentos
    map = L.map('map', { zoomControl: false }).setView([-33.1333, -58.3000], 14);

    // Controles de zoom abajo a la derecha
    L.control.zoom({ position: 'bottomright' }).addTo(map);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap'
    }).addTo(map);

    // Evento táctil/click al tocar sobre el mapa
    map.on('click', (e) => {
        const { lat, lng } = e.latlng;

        // Asignar coordenadas a los inputs
        document.getElementById('latitud').value = lat.toFixed(6);
        document.getElementById('longitud').value = lng.toFixed(6);

        // Mover o crear marcador temporal
        if (activeMarker) {
            activeMarker.setLatLng([lat, lng]);
        } else {
            activeMarker = L.marker([lat, lng], { draggable: true }).addTo(map);
        }

        // Abrir panel inferior animado
        abrirMenuReporte();
    });
}

function abrirMenuReporte() {
    const sheet = document.getElementById('report-sheet');
    const badge = document.getElementById('instruction-badge');
    
    if (sheet) sheet.classList.remove('translate-y-full');
    if (badge) badge.classList.add('hidden');
}

function cerrarMenuReporte() {
    const sheet = document.getElementById('report-sheet');
    if (sheet) sheet.classList.add('translate-y-full');
}

function setupImagePreview() {
    const inputFoto = document.getElementById('input-foto');
    const previewContainer = document.getElementById('preview-container');
    const previewImg = document.getElementById('foto-preview');

    if (inputFoto) {
        inputFoto.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    previewImg.src = event.target.result;
                    previewContainer.classList.remove('hidden');
                };
                reader.readAsDataURL(file);
            }
        });
    }
}

async function cargarReportesPublicos() {
    try {
        const res = await fetch('/api/reportes');
        if (!res.ok) return;
        const reportes = await res.json();
        reportesCache = reportes;

        const colorGravedad = { alta: '#ef4444', media: '#f59e0b', baja: '#10b981' };

        reportes.forEach(r => {
            if (!r.latitud || !r.longitud) return;

            const color = colorGravedad[r.gravedad] || '#3b82f6';

            const circle = L.circleMarker([r.latitud, r.longitud], {
                radius: 9,
                fillColor: color,
                color: '#ffffff',
                weight: 2.5,
                fillOpacity: 0.9
            }).addTo(map);

            circle.bindPopup(`
                <div class="p-1 font-sans text-xs">
                    ${r.foto_url ? `<img src="${r.foto_url}" class="w-full h-24 object-cover rounded-lg mb-2">` : ''}
                    <p class="font-black text-slate-900">${r.titulo}</p>
                    <p class="text-[10px] text-slate-500">${r.categoria} • <span class="uppercase font-bold">${r.gravedad}</span></p>
                </div>
            `);
        });
    } catch (err) {
        console.error('Error cargando marcadores:', err);
    }
}

async function enviarReporte(e) {
    e.preventDefault();
    const btnSubmit = document.getElementById('btn-submit');
    btnSubmit.disabled = true;
    btnSubmit.innerHTML = `<i class="fa-solid fa-spinner animate-spin"></i> <span>Enviando...</span>`;

    // Uso de FormData para enviar tanto texto como la fotografía
    const formData = new FormData();
    formData.append('latitud', document.getElementById('latitud').value);
    formData.append('longitud', document.getElementById('longitud').value);
    formData.append('titulo', document.getElementById('titulo').value);
    formData.append('categoria', document.getElementById('categoria').value);
    formData.append('gravedad', document.getElementById('gravedad').value);
    formData.append('descripcion', document.getElementById('descripcion').value);

    const inputFoto = document.getElementById('input-foto');
    if (inputFoto && inputFoto.files[0]) {
        formData.append('foto', inputFoto.files[0]);
    }

    try {
        const res = await fetch('/api/reportes', {
            method: 'POST',
            body: formData // No se pone 'Content-Type', el navegador lo asigna automáticamente
        });

        if (!res.ok) {
            const errorData = await res.json().catch(() => ({}));
            throw new Error(errorData.error || `Error del servidor (${res.status})`);
        }

        // Limpiar formulario y cerrar panel
        document.getElementById('form-reporte-mobile').reset();
        document.getElementById('preview-container').classList.add('hidden');
        cerrarMenuReporte();

        // Eliminar marcador temporal
        if (activeMarker) {
            map.removeLayer(activeMarker);
            activeMarker = null;
        }

        // Mostrar tick verde animado y recargar marcadores
        mostrarModalExito();
        cargarReportesPublicos();
    } catch (err) {
        console.error('Detalle del error:', err);
        alert(`No se pudo guardar el reporte: ${err.message}`);
    } finally {
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = `<i class="fa-solid fa-paper-plane"></i> <span>Publicar Reporte Ciudadano</span>`;
    }
}

function mostrarModalExito() {
    const modal = document.getElementById('modal-success');
    if (modal) modal.classList.remove('hidden');
}

function cerrarModalExito() {
    const modal = document.getElementById('modal-success');
    if (modal) modal.classList.add('hidden');
}