import os
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import inspect, text

app = Flask(__name__)

# Llave secreta para manejar sesiones de forma segura
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'eco_mapa_secret_key_2026_fray_bentos')

# Configuración de base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///ecomapa.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Soporte para PostgreSQL en Render
if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)

UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

# Modelo de Administradores
class UsuarioAdmin(db.Model):
    __tablename__ = 'usuario_admin'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

# Modelo de Reportes
class Reporte(db.Model):
    __tablename__ = 'reporte'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    gravedad = db.Column(db.String(20), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    latitud = db.Column(db.Float, nullable=False)
    longitud = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(20), default='Pendiente')
    foto_url = db.Column(db.String(300), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        fecha_str = self.fecha_creacion.strftime('%d/%m/%Y %H:%M') if self.fecha_creacion else 'Reciente'
        return {
            'id': self.id,
            'titulo': self.titulo,
            'categoria': self.categoria,
            'gravedad': self.gravedad,
            'descripcion': self.descripcion,
            'latitud': self.latitud,
            'longitud': self.longitud,
            'estado': self.estado,
            'foto_url': self.foto_url,
            'fecha': fecha_str
        }

# Decorador para proteger las rutas de administrador
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Inicialización de BD y creación del Administrador por defecto
with app.app_context():
    db.create_all()
    try:
        inspector = inspect(db.engine)
        columnas = [col['name'] for col in inspector.get_columns('reporte')]
        if 'fecha_creacion' not in columnas:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE reporte ADD COLUMN fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                conn.commit()
    except Exception as e:
        print("Verificación de esquema completada:", e)

    # Crear cuenta de admin por defecto si no existe ninguna
    if not UsuarioAdmin.query.first():
        admin_defecto = UsuarioAdmin(
            email='admin@ecomapa.org',
            password_hash=generate_password_hash('admin123')
        )
        db.session.add(admin_defecto)
        db.session.commit()
        print("Administrador por defecto creado: admin@ecomapa.org / admin123")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET'])
def login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    datos = request.get_json() or {}
    email = datos.get('email', '').strip().lower()
    password = datos.get('password', '').strip()

    if not email or not password:
        return jsonify({'error': 'Por favor completa todos los campos'}), 400

    admin = UsuarioAdmin.query.filter_by(email=email).first()

    if admin and check_password_hash(admin.password_hash, password):
        session['admin_logged_in'] = True
        session['admin_email'] = admin.email
        return jsonify({'mensaje': 'Inicio de sesión exitoso', 'redirect': '/admin'}), 200
    else:
        return jsonify({'error': 'Correo o contraseña incorrectos'}), 401

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_email', None)
    return redirect(url_for('index'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    reportes = Reporte.query.order_by(Reporte.id.desc()).all()
    return render_template('admin.html', reportes=reportes, admin_email=session.get('admin_email'))

@app.route('/api/reportes/<int:reporte_id>/estado', methods=['PUT'])
@admin_required
def cambiar_estado(reporte_id):
    try:
        reporte = Reporte.query.get_or_404(reporte_id)
        datos = request.get_json() or {}
        nuevo_estado = datos.get('estado')
        
        if nuevo_estado in ['Pendiente', 'En Proceso', 'Resuelto']:
            reporte.estado = nuevo_estado
            db.session.commit()
            return jsonify({'mensaje': 'Estado actualizado con éxito'}), 200
        return jsonify({'error': 'Estado no válido'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/reportes/<int:reporte_id>', methods=['DELETE'])
@admin_required
def eliminar_reporte(reporte_id):
    try:
        reporte = Reporte.query.get_or_404(reporte_id)
        db.session.delete(reporte)
        db.session.commit()
        return jsonify({'mensaje': 'Reporte eliminado correctamente'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/reportes', methods=['GET'])
def obtener_reportes():
    try:
        reportes = Reporte.query.order_by(Reporte.id.desc()).all()
        return jsonify([r.to_dict() for r in reportes]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reportes', methods=['POST'])
def crear_reporte():
    try:
        datos = request.form if request.form else (request.get_json() or {})

        titulo = datos.get('titulo')
        latitud = datos.get('latitud')
        longitud = datos.get('longitud')

        if not titulo or latitud is None or longitud is None:
            return jsonify({'error': 'Faltan campos obligatorios'}), 400

        foto_path = None
        if 'foto' in request.files:
            file = request.files['foto']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(save_path)
                foto_path = f'/{UPLOAD_FOLDER}/{filename}'

        nuevo_reporte = Reporte(
            titulo=str(titulo),
            categoria=str(datos.get('categoria', 'Otro')),
            gravedad=str(datos.get('gravedad', 'baja')),
            descripcion=str(datos.get('descripcion', '')),
            latitud=float(latitud),
            longitud=float(longitud),
            estado='Pendiente',
            foto_url=foto_path,
            fecha_creacion=datetime.now()
        )

        db.session.add(nuevo_reporte)
        db.session.commit()

        return jsonify({'mensaje': 'Reporte guardado con éxito', 'reporte': nuevo_reporte.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al guardar en BD: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)