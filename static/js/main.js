// Control de Pantalla de Inicio y Transición Fluida
document.addEventListener('DOMContentLoaded', () => {
    const splash = document.getElementById('splash-screen');
    const btnEntrar = document.getElementById('btn-entrar');
    const mapContainer = document.getElementById('map-container');

    btnEntrar.addEventListener('click', () => {
        // Transición de salida de la bienvenida
        splash.classList.add('splash-hidden');
        
        // Transición de entrada del mapa
        setTimeout(() => {
            mapContainer.classList.add('visible');
            map.invalidateSize(); // Renderiza correctamente el mapa de Leaflet
        }, 400);
    });
});

// Control visual del campo "Otro problema"
const selectCategoria = document.getElementById('select_categoria');
const divOtroProblema = document.getElementById('divOtroProblema');
const inputOtroProblema = document.getElementById('inputOtroProblema');

selectCategoria.addEventListener('change', function() {
    if (this.value === 'otro') {
        divOtroProblema.classList.remove('d-none');
        inputOtroProblema.required = true;
    } else {
        divOtroProblema.classList.add('d-none');
        inputOtroProblema.required = false;
    }
});

// Inicialización del Mapa
const map = L.map('map').setView([-33.12, -58.30], 13);
const modalElement = new bootstrap.Modal(document.getElementById('reporteModal'));

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
                const imgHtml = rep.foto_path ? `<img src="/static/${rep.foto_path}" class="img-fluid rounded-3 mt-2 shadow-sm" style="max-height:130px; width:100%; object-fit:cover;">` : '';
                
                L.marker([rep.latitud, rep.longitud], { icon: icon })
                    .bindPopup(`
                        <div style="max-width:240px;" class="p-1">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span class="badge ${badgeColor}">${rep.estado}</span>
                                <span class="badge bg-secondary">${rep.gravedad}</span>
                            </div>
                            <h6 class="fw-bold mb-1 text-dark">${rep.categoria}</h6>
                            <p class="small text-muted mb-2">${rep.descripcion}</p>
                            ${imgHtml}
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
    selectCategoria.value = "";
    divOtroProblema.classList.add('d-none');
    inputOtroProblema.value = "";
    modalElement.show();
});

// Envío del Formulario con Alerta SweetAlert2
document.getElementById('formReporte').addEventListener('submit', function(e) {
    e.preventDefault();
    const formData = new FormData(this);

    // Si seleccionó "Otro", empaquetamos el texto personalizado en la categoría 1
    if (selectCategoria.value === 'otro') {
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
        if (data.status === 'success') {
            modalElement.hide();
            this.reset();
            divOtroProblema.classList.add('d-none');
            cargarReportes();
            Swal.fire({
                icon: 'success',
                title: '¡Reporte Enviado!',
                text: 'El incidente fue registrado exitosamente en el mapa.',
                confirmColor: '#0d9488',
                customClass: { popup: 'rounded-4' }
            });
        }
    });
});

cargarReportes();