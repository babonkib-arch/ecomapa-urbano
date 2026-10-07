import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from sqlalchemy import inspect, text

app = Flask(__name__)

# Configuración de base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///ecomapa.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Soporte para PostgreSQL en Render (si empieza por postgres:// cambiar a postgresql://)
if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)

UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

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

# Asegurar que la tabla y columnas existan en la BD sin romper Render
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
        print("Migración interna no requerida o completada:", e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

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
            return jsonify({'error': 'Faltan campos obligatorios (título, latitud o longitud)'}), 400

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
            estado=str(datos.get('estado', 'Pendiente')),
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