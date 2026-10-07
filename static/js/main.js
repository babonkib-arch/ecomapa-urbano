let map;
let activeMarker = null;

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
    map = L.map('map', { zoomControl: false }).setView([-33.1333, -58.3000], 14);

    L.control.zoom({ position: 'bottomright' }).addTo(map);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap'
    }).addTo(map);

    map.on('click', (e) => {
        const { lat, lng } = e.latlng;

        document.getElementById('latitud').value = lat.toFixed(6);
        document.getElementById('longitud').value = lng.toFixed(6);

        if (activeMarker) {
            activeMarker.setLatLng([lat, lng]);
        } else {
            activeMarker = L.marker([lat, lng], { draggable: true }).addTo(map);
        }

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
    const badge = document.getElementById('instruction-badge');
    if (sheet) sheet.classList.add('translate-y-full');
    if (badge) badge.classList.remove('hidden');
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

        const colorGravedad = { alta: '#ef4444', media: '#f59e0b', baja: '#10b981' };

        reportes.forEach(r => {
            if (!r.latitud || !r.longitud) return;

            const color = colorGravedad[r.gravedad] || '#10b981';

            const circle = L.circleMarker([r.latitud, r.longitud], {
                radius: 8,
                fillColor: color,
                color: '#ffffff',
                weight: 2,
                fillOpacity: 0.9
            }).addTo(map);

            const mensajeShare = encodeURIComponent(`🚨 Alerta en EcoMapa FB: ${r.titulo} (${r.categoria})`);
            const pageUrl = encodeURIComponent(window.location.href);

            circle.bindPopup(`
                <div class="p-2 font-sans text-xs max-w-[220px] text-slate-800 space-y-2">
                    ${r.foto_url ? `<img src="${r.foto_url}" class="w-full h-28 object-cover rounded-xl border border-slate-200">` : ''}
                    <div>
                        <h4 class="font-bold text-xs text-slate-900 leading-snug">${r.titulo}</h4>
                        <div class="flex items-center gap-1 mt-1">
                            <span class="px-2 py-0.5 rounded-full text-[9px] font-bold bg-slate-100 text-slate-700">${r.categoria}</span>
                            <span class="px-2 py-0.5 rounded-full text-[9px] font-bold text-white uppercase" style="background-color: ${color}">${r.gravedad}</span>
                        </div>
                    </div>
                    ${r.descripcion ? `<p class="text-slate-600 text-[11px] bg-slate-50 p-2 rounded-lg border border-slate-100">${r.descripcion}</p>` : ''}
                    
                    <div class="border-t border-slate-200 pt-1.5 text-[10px] text-slate-500 space-y-0.5">
                        <p><i class="fa-regular fa-clock text-emerald-600"></i> ${r.fecha}</p>
                        <p><i class="fa-solid fa-location-dot text-emerald-600"></i> ${r.latitud.toFixed(4)}, ${r.longitud.toFixed(4)}</p>
                    </div>

                    <div class="border-t border-slate-200 pt-1.5 flex items-center justify-between">
                        <span class="text-[9px] font-bold text-slate-400 uppercase">Compartir:</span>
                        <div class="flex gap-2 text-sm">
                            <a href="https://api.whatsapp.com/send?text=${mensajeShare}%20${pageUrl}" target="_blank" class="text-emerald-600"><i class="fa-brands fa-whatsapp"></i></a>
                            <a href="https://www.facebook.com/sharer/sharer.php?u=${pageUrl}" target="_blank" class="text-blue-600"><i class="fa-brands fa-facebook"></i></a>
                            <a href="https://twitter.com/intent/tweet?text=${mensajeShare}&url=${pageUrl}" target="_blank" class="text-slate-800"><i class="fa-brands fa-x-twitter"></i></a>
                        </div>
                    </div>
                </div>
            `);
        });
    } catch (err) {
        console.error('Error cargando los puntos:', err);
    }
}

async function enviarReporte(e) {
    e.preventDefault();
    const btnSubmit = document.getElementById('btn-submit');
    btnSubmit.disabled = true;
    btnSubmit.innerHTML = `<i class="fa-solid fa-spinner animate-spin"></i> <span>Guardando reporte...</span>`;

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
            body: formData
        });

        const respuestaData = await res.json();

        if (!res.ok) {
            throw new Error(respuestaData.error || 'Error al guardar el reporte');
        }

        document.getElementById('form-reporte-mobile').reset();
        document.getElementById('preview-container').classList.add('hidden');
        cerrarMenuReporte();

        if (activeMarker) {
            map.removeLayer(activeMarker);
            activeMarker = null;
        }

        mostrarModalExito();
        cargarReportesPublicos();
    } catch (err) {
        alert(`Error: ${err.message}`);
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