let adminMap;
let adminMarkers = [];

document.addEventListener('DOMContentLoaded', () => {
    initAdminMap();
    cargarReportesAdmin();

    const formEditar = document.getElementById('form-editar-reporte');
    if (formEditar) {
        formEditar.addEventListener('submit', guardarEdicionReporte);
    }
});

function initAdminMap() {
    // Inicializar mapa centrado en Fray Bentos
    adminMap = L.map('admin-map').setView([-33.1333, -58.3000], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap'
    }).addTo(adminMap);
}

async function cargarReportesAdmin() {
    try {
        const res = await fetch('/api/reportes');
        if (!res.ok) throw new Error('Error al obtener datos');
        const reportes = await res.json();

        actualizarKPIs(reportes);
        renderizarMapaAdmin(reportes);
        renderizarTablaAdmin(reportes);
        renderizarTarjetasMobile(reportes);
    } catch (err) {
        console.error('Error:', err);
    }
}

function actualizarKPIs(reportes) {
    document.getElementById('kpi-total').textContent = reportes.length;
    document.getElementById('kpi-pendientes').textContent = reportes.filter(r => (r.estado || 'Pendiente') === 'Pendiente').length;
    document.getElementById('kpi-resueltos').textContent = reportes.filter(r => r.estado === 'Resuelto').length;
    document.getElementById('kpi-urgentes').textContent = reportes.filter(r => r.gravedad === 'alta').length;
}

function renderizarMapaAdmin(reportes) {
    // Limpiar marcadores
    adminMarkers.forEach(m => adminMap.removeLayer(m));
    adminMarkers = [];

    const colorGravedad = { alta: '#ef4444', media: '#f59e0b', baja: '#10b981' };

    reportes.forEach(r => {
        if (!r.latitud || !r.longitud) return;

        const color = colorGravedad[r.gravedad] || '#3b82f6';
        const marker = L.circleMarker([r.latitud, r.longitud], {
            radius: 8,
            fillColor: color,
            color: '#ffffff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.9
        }).addTo(adminMap);

        marker.bindPopup(`
            <div class="p-1 font-sans text-xs">
                <p class="font-bold text-slate-900 mb-1">${r.titulo}</p>
                <p class="text-[11px] text-slate-500">${r.categoria} • <span class="uppercase font-semibold">${r.gravedad}</span></p>
            </div>
        `);

        adminMarkers.push(marker);
    });
}

function renderizarTablaAdmin(reportes) {
    const tbody = document.getElementById('tabla-reportes-body');
    if (!tbody) return;

    if (reportes.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="py-6 text-center text-slate-400">No hay reportes registrados aún.</td></tr>`;
        return;
    }

    tbody.innerHTML = reportes.map(r => `
        <tr class="hover:bg-slate-50/80 transition">
            <td class="py-3 px-4">
                ${r.foto_url 
                    ? `<img src="${r.foto_url}" class="w-12 h-12 object-cover rounded-xl border border-slate-200">` 
                    : `<div class="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center text-slate-400 text-xs"><i class="fa-solid fa-image"></i></div>`}
            </td>
            <td class="py-3 px-4">
                <p class="font-bold text-slate-900">${r.titulo}</p>
                <span class="text-[10px] text-slate-500">${r.categoria}</span>
            </td>
            <td class="py-3 px-4">
                <span class="px-2.5 py-1 rounded-full text-[10px] font-extrabold uppercase ${getBadgeGravedad(r.gravedad)}">
                    ${r.gravedad}
                </span>
            </td>
            <td class="py-3 px-4">
                <span class="px-2.5 py-1 rounded-full text-[10px] font-bold ${getBadgeEstado(r.estado || 'Pendiente')}">
                    ${r.estado || 'Pendiente'}
                </span>
            </td>
            <td class="py-3 px-4 text-right space-x-1">
                <button onclick="abrirModalEditar('${r.id}')" class="p-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition active:scale-95">
                    <i class="fa-solid fa-pen text-xs"></i>
                </button>
                <button onclick="eliminarReporte('${r.id}')" class="p-2 bg-rose-50 hover:bg-rose-100 text-rose-600 rounded-lg transition active:scale-95">
                    <i class="fa-solid fa-trash-can text-xs"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function renderizarTarjetasMobile(reportes) {
    const contenedor = document.getElementById('contenedor-tarjetas-mobile');
    if (!contenedor) return;

    if (reportes.length === 0) {
        contenedor.innerHTML = `<div class="p-6 text-center text-slate-400">No hay reportes registrados.</div>`;
        return;
    }

    contenedor.innerHTML = reportes.map(r => `
        <div class="p-4 flex flex-col space-y-3">
            <div class="flex items-start justify-between">
                <div class="flex items-center space-x-3">
                    ${r.foto_url 
                        ? `<img src="${r.foto_url}" class="w-14 h-14 object-cover rounded-2xl border border-slate-200">` 
                        : `<div class="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-400"><i class="fa-solid fa-image"></i></div>`}
                    <div>
                        <h4 class="font-black text-slate-900 text-sm leading-tight">${r.titulo}</h4>
                        <p class="text-[11px] text-slate-500 mt-0.5">${r.categoria}</p>
                    </div>
                </div>
            </div>

            <div class="flex items-center justify-between pt-1">
                <div class="flex items-center space-x-2">
                    <span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase ${getBadgeGravedad(r.gravedad)}">
                        ${r.gravedad}
                    </span>
                    <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold ${getBadgeEstado(r.estado || 'Pendiente')}">
                        ${r.estado || 'Pendiente'}
                    </span>
                </div>

                <div class="flex items-center space-x-2">
                    <button onclick="abrirModalEditar('${r.id}')" class="px-3 py-1.5 bg-slate-100 text-slate-700 font-bold rounded-xl text-xs active:scale-95">
                        Editar
                    </button>
                    <button onclick="eliminarReporte('${r.id}')" class="p-1.5 bg-rose-50 text-rose-600 rounded-xl text-xs active:scale-95">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

function getBadgeGravedad(gravedad) {
    switch (gravedad) {
        case 'alta': return 'bg-rose-100 text-rose-700 border border-rose-200';
        case 'media': return 'bg-amber-100 text-amber-700 border border-amber-200';
        default: return 'bg-emerald-100 text-emerald-700 border border-emerald-200';
    }
}

function getBadgeEstado(estado) {
    switch (estado) {
        case 'Resuelto': return 'bg-brand-500 text-white';
        case 'En Proceso': return 'bg-sky-500 text-white';
        default: return 'bg-slate-200 text-slate-700';
    }
}

async function abrirModalEditar(id) {
    try {
        const res = await fetch(`/api/reportes/${id}`);
        if (!res.ok) throw new Error('No se pudo cargar el reporte');
        const r = await res.json();

        document.getElementById('edit-id').value = r.id;
        document.getElementById('edit-titulo').value = r.titulo;
        document.getElementById('edit-categoria').value = r.categoria;
        document.getElementById('edit-gravedad').value = r.gravedad;
        document.getElementById('edit-estado').value = r.estado || 'Pendiente';
        document.getElementById('edit-descripcion').value = r.descripcion;

        document.getElementById('modal-editar').classList.remove('hidden');
    } catch (err) {
        alert('Error al obtener datos del reporte');
    }
}

function cerrarModalEditar() {
    document.getElementById('modal-editar').classList.add('hidden');
}

async function guardarEdicionReporte(e) {
    e.preventDefault();
    const id = document.getElementById('edit-id').value;

    const payload = {
        titulo: document.getElementById('edit-titulo').value,
        categoria: document.getElementById('edit-categoria').value,
        gravedad: document.getElementById('edit-gravedad').value,
        estado: document.getElementById('edit-estado').value,
        descripcion: document.getElementById('edit-descripcion').value
    };

    try {
        const res = await fetch(`/api/reportes/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error('Error al actualizar');
        
        cerrarModalEditar();
        cargarReportesAdmin();
    } catch (err) {
        alert('Error al guardar cambios');
    }
}

async function eliminarReporte(id) {
    if (!confirm('¿Seguro que deseas eliminar este reporte?')) return;

    try {
        const res = await fetch(`/api/reportes/${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Error al eliminar');
        cargarReportesAdmin();
    } catch (err) {
        alert('No se pudo eliminar el reporte');
    }
}