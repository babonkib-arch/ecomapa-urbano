<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel Admin - EcoMapa</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-light">

    <nav class="navbar navbar-dark bg-dark px-4 py-3">
        <div class="container-fluid">
            <span class="navbar-brand fw-bold"><i class="fa-solid fa-user-shield me-2"></i>Panel Admin EcoMapa</span>
            <a href="/" class="btn btn-outline-light btn-sm rounded-pill px-3">Ver Mapa Público</a>
        </div>
    </nav>

    <div class="container my-5">
        <div class="card border-0 shadow-sm p-4 bg-white rounded-3">
            <h4 class="fw-bold mb-4 text-secondary"><i class="fa-solid fa-list-check me-2"></i>Gestión de Incidencias</h4>

            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="table-light">
                        <tr>
                            <th>ID</th>
                            <th>Categoría</th>
                            <th>Descripción</th>
                            <th>Evidencia</th>
                            <th>Gravedad</th>
                            <th>Estado</th>
                            <th class="text-end">Acción</th>
                        </tr>
                    </thead>
                    <!-- El JavaScript cargará los datos aquí -->
                    <tbody id="tabla-admin-body">
                        <tr>
                            <td colspan="7" class="text-center py-3 text-muted">Cargando datos...</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Script Admin JS -->
    <script src="js/admin.js"></script>
</body>
</html>