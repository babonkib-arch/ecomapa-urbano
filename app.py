import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuración de base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///ecomapa.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuración de carpeta para archivos subidos
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

# Modelo de datos extendido con fecha de creación
class Reporte(db.Model):
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
        fecha_fmt = self.fecha_creacion.strftime('%d/%m/%Y a las %H:%M hs') if self.fecha_creacion else 'Sin fecha'
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
            'fecha': fecha_fmt
        }

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/api/reportes', methods=['GET'])
def obtener_reportes():
    try:
        reportes = Reporte.query.order_by(Reporte.fecha_creacion.desc()).all()
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
            titulo=titulo,
            categoria=datos.get('categoria', 'Otro'),
            gravedad=datos.get('gravedad', 'baja'),
            descripcion=datos.get('descripcion', ''),
            latitud=float(latitud),
            longitud=float(longitud),
            estado=datos.get('estado', 'Pendiente'),
            foto_url=foto_path,
            fecha_creacion=datetime.utcnow()
        )

        db.session.add(nuevo_reporte)
        db.session.commit()

        return jsonify({'mensaje': 'Reporte guardado con éxito', 'reporte': nuevo_reporte.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)