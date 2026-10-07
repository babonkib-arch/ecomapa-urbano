let map, markerSeleccionado, reportesMarkersGroup;
let imagenBase64 = "";

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    cargarReportes();

    // Listener para abrir cámara y capturar preview
    const inputFoto = document.getElementById('input-foto');
    if (inputFoto) {
        inputFoto.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (event) {
                    imagenBase64 = event.target.result;
                    const preview = document.getElementById('foto-preview');
                    preview.src = imagenBase64;
                    document.getElementById('preview-container').classList.remove('hidden');
                };
                reader.readAsDataURL(file);
            }
        });
    }

    document.getElementById('form-reporte').addEventListener('submit', guardarReporte);
});

function initMap() {
    map = L.map('map').setView([-33.1325, -58.2989], 14);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap | EcoMapa Fray Bentos'
    }).addTo(map);

    reportesMarkersGroup = L.layerGroup().addTo(map);

    map.on('click', (e) => {
        const { lat, lng } = e.latlng;
        document.getElementById('latitud').value = lat.toFixed(6);
        document.getElementById('longitud').value = lng.toFixed(6);

        if (markerSeleccionado) map.removeLayer(markerSeleccionado);

        markerSeleccionado = L.marker([lat, lng], {
            icon: L.divIcon({
                className: 'custom-pin-temp',
                html: `<div style="background-color: #0284c7; width: 18px; height: 18px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 10px rgba(0,0,0,0.3);"></div>`,
                iconSize: [18, 18],
                iconAnchor: [9, 9]
            })
        }).addTo(map);
    });
}

async function cargarReportes() {
    try {
        const res = await fetch('/api/reportes');
        const reportes = await res.json();
        reportesMarkersGroup.clearLayers();

        reportes.forEach(r => {
            const colorGravedad = {
                'baja': '#10b981',
                'media': '#f59e0b',
                'alta': '#ef4444'
            }[r.gravedad] || '#6b7280';

            const marker = L.marker([r.latitud, r.longitud], {
                icon: L.divIcon({
                    className: 'custom-pin',
                    html: `<div style="background-color: ${colorGravedad}; width: 22px; height: 22px; border-radius: 50%; border: 3px solid white; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3);"></div>`,
                    iconSize: [22, 22],
                    iconAnchor: [11, 11]
                })
            });

            // Enlace exacto a Google Maps
            const googleMapsUrl = `https://www.google.com/maps?q=${r.latitud},${r.longitud}`;
            const shareUrl = window.location.origin + '/#mapa-section';
            const shareText = encodeURIComponent(`🚨 Incidente en EcoMapa Fray Bentos: ${r.titulo}`);

            // Estructura del Popup Premium con Foto, Fecha, Hora y Google Maps
            const popupHtml = `
                <div style="font-family: sans-serif; max-width: 260px;">
                    ${r.imagen_url ? `<img src="${r.imagen_url}" style="width:100%; height:130px; object-fit:cover; border-radius:10px; margin-bottom:8px;">` : ''}
                    
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                        <span style="font-size:10px; font-weight:bold; background:#f1f5f9; padding:2px 6px; border-radius:4px; text-transform:uppercase;">${r.categoria}</span>
                        <span style="font-size:10px; font-weight:bold; color:${colorGravedad}; text-transform:uppercase;">● ${r.gravedad}</span>
                    </div>

                    <h4 style="font-size:14px; font-weight:bold; margin:4px 0; color:#0f172a;">${r.titulo}</h4>
                    <p style="font-size:11px; color:#475569; margin-bottom:6px; line-height:1.3;">${r.descripcion}</p>
                    
                    <div style="font-size:10px; color:#94a3b8; margin-bottom:8px;">
                        <i class="fa-regular fa-clock"></i> <strong>Fecha/Hora:</strong> ${r.fecha_creacion}
                    </div>

                    <!-- Botón Google Maps -->
                    <a href="${googleMapsUrl}" target="_blank" style="display:block; text-align:center; background:#ea4335; color:white; font-size:11px; font-weight:bold; padding:6px; border-radius:6px; text-decoration:none; margin-bottom:8px;">
                        📍 Ver en Google Maps
                    </a>

                    <!-- Botones de Redes Sociales -->
                    <div style="border-top:1px solid #e2e8f0; padding-top:6px; display:flex; gap:4px; flex-wrap:wrap;">
                        <a href="https://api.whatsapp.com/send?text=${shareText}%20${encodeURIComponent(shareUrl)}" target="_blank" style="background:#25D366; color:white; font-size:10px; padding:4px 6px; border-radius:4px; text-decoration:none; font-weight:bold;">WhatsApp</a>
                        <a href="https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}" target="_blank" style="background:#1877F2; color:white; font-size:10px; padding:4px 6px; border-radius:4px; text-decoration:none; font-weight:bold;">Facebook</a>
                        <a href="https://twitter.com/intent/tweet?text=${shareText}&url=${encodeURIComponent(shareUrl)}" target="_blank" style="background:#000; color:white; font-size:10px; padding:4px 6px; border-radius:4px; text-decoration:none; font-weight:bold;">X</a>
                        <button onclick="navigator.clipboard.writeText('${googleMapsUrl}'); alert('¡Ubicación de Google Maps copiada!');" style="background:#64748b; color:white; font-size:10px; padding:4px 6px; border-radius:4px; border:none; cursor:pointer;">Copiar Link</button>
                    </div>
                </div>
            `;

            marker.bindPopup(popupHtml);
            reportesMarkersGroup.addLayer(marker);
        });
    } catch (e) {
        console.error("Error al cargar reportes:", e);
    }
}

async function guardarReporte(e) {
    e.preventDefault();

    const data = {
        latitud: document.getElementById('latitud').value,
        longitud: document.getElementById('longitud').value,
        titulo: document.getElementById('titulo').value,
        categoria: document.getElementById('categoria').value,
        gravedad: document.getElementById('gravedad').value,
        descripcion: document.getElementById('descripcion').value,
        imagen_url: imagenBase64
    };

    if (!data.latitud || !data.longitud) {
        alert("Haz clic sobre el mapa para indicar la ubicación.");
        return;
    }

    const res = await fetch('/api/reportes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    if (res.ok) {
        alert("¡Reporte y foto registrados con éxito!");
        document.getElementById('form-reporte').reset();
        document.getElementById('preview-container').classList.add('hidden');
        imagenBase64 = "";
        if (markerSeleccionado) map.removeLayer(markerSeleccionado);
        cargarReportes();
    }
}