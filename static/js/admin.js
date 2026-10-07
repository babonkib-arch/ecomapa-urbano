document.addEventListener('DOMContentLoaded', () => {
    cargarReportesAdmin();
});

async function cargarReportesAdmin() {
    try {
        const response = await fetch('/api/reportes');
        if (response.status === 401) {
            window.location.href = '/login';
            return;
        }

        const reportes = await response.json();
        renderTabla(reportes);
        actualizarEstadisticas(reportes);
    } catch (error) {
        console.error("Error al cargar reportes admin:", error);
    }
}

function renderTabla(reportes) {
    const tbody = document.getElementById('tabla-body');
    tbody.innerHTML = '';

    if (reportes.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center py-8 text-slate-400">No hay reportes registrados.</td></tr>`;
        return;
    }

    reportes.forEach(r => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-slate-50 transition';

        const badgeEstado = r.estado === 'resuelto'
            ? `<span class="bg-emerald-100 text-emerald-800 text-xs font-bold px-2.5 py-1 rounded-full">Resuelto</span>`
            : `<span class="bg-amber-100 text-amber-800 text-xs font-bold px-2.5 py-1 rounded-full">Pendiente</span>`;

        const badgeGravedad = {
            'baja': '<span class="text-emerald-600 font-bold">● Baja</span>',
            'media': '<span class="text-amber-600 font-bold">● Media</span>',
            'alta': '<span class="text-rose-600 font-bold">● Alta</span>'
        }[r.gravedad] || r.gravedad;

        const fechaFormatted = new Date(r.fecha_creacion).toLocaleDateString('es-UY', {
            day: '2-digit', month: '2-digit', year: 'numeric'
        });

        tr.innerHTML = `
            <td class="py-4 px-6 font-mono text-xs text-slate-500">#${r.id}</td>
            <td class="py-4 px-6">
                <div class="font-bold text-slate-900">${r.titulo}</div>
                <div class="text-xs text-slate-500">${r.categoria}</div>
            </td>
            <td class="py-4 px-6 text-xs">${badgeGravedad}</td>
            <td class="py-4 px-6">${badgeEstado}</td>
            <td class="py-4 px-6 text-xs text-slate-500">${fechaFormatted}</td>
            <td class="py-4 px-6 text-right space-x-2">
                ${r.estado !== 'resuelto' ? `
                    <button onclick="resolverReporte(${r.id})" class="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition">
                        Resolver
                    </button>
                ` : ''}
                <button onclick="borrarReporte(${r.id})" class="bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition">
                    Borrar
                </button>
            </td>
        `;

        tbody.appendChild(tr);
    });
}

function actualizarEstadisticas(reportes) {
    document.getElementById('stat-total').innerText = reportes.length;
    document.getElementById('stat-pendientes').innerText = reportes.filter(r => r.estado === 'pendiente').length;
    document.getElementById('stat-resueltos').innerText = reportes.filter(r => r.estado === 'resuelto').length;
}

// Acción: Resolver Reporte
async function resolverReporte(id) {
    if (!confirm(`¿Confirmas marcar el reporte #${id} como RESUELTO?`)) return;

    try {
        const response = await fetch(`/api/reportes/${id}/resolver`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' }
        });

        if (response.ok) {
            cargarReportesAdmin();
        } else {
            alert("No se pudo actualizar el estado del reporte.");
        }
    } catch (error) {
        console.error("Error al resolver:", error);
    }
}

// Acción: Eliminar Reporte definitivamente de PostgreSQL
async function borrarReporte(id) {
    if (!confirm(`¿Estás seguro de ELIMINAR DEFINITIVAMENTE el reporte #${id}? Esta acción borrará el registro en Supabase.`)) return;

    try {
        const response = await fetch(`/api/reportes/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            cargarReportesAdmin();
        } else {
            alert("No se pudo eliminar el reporte.");
        }
    } catch (error) {
        console.error("Error al eliminar:", error);
    }
}