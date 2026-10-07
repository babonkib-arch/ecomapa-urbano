import os
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "eco_mapa_fray_bentos_secret_key_2026")
DATABASE_URL = os.getenv("DATABASE_URL")

# Lista blanca de 4 Administradores autorizados
ADMINS_PERMITIDOS = [
    "admin1@gmail.com",
    "admin2@gmail.com",
    "admin3@gmail.com",
    "admin4@gmail.com"
]

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Tabla de Reportes con soporte para Imagen URL
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reportes (
            id SERIAL PRIMARY KEY,
            titulo VARCHAR(150) NOT NULL,
            descripcion TEXT NOT NULL,
            categoria VARCHAR(50) NOT NULL,
            gravedad VARCHAR(20) NOT NULL CHECK (gravedad IN ('baja', 'media', 'alta')),
            latitud DOUBLE PRECISION NOT NULL,
            longitud DOUBLE PRECISION NOT NULL,
            imagen_url TEXT,
            estado VARCHAR(20) DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'resuelto')),
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_resolucion TIMESTAMP
        );
    """)

    # Tabla de Usuarios Admin por Email
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
    """)

    # Sembrar Administradores por defecto si no existen
    default_pass = generate_password_hash("AdminEco2026!")
    for email in ADMINS_PERMITIDOS:
        cur.execute("SELECT id FROM usuarios WHERE email = %s;", (email,))
        if not cur.fetchone():
            cur.execute("INSERT INTO usuarios (email, password_hash) VALUES (%s, %s);", (email, default_pass))

    conn.commit()
    cur.close()
    conn.close()

try:
    init_db()
except Exception as e:
    print(f"[BD ERROR] {e}")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return jsonify({'error': 'No autorizado'}), 401
        return f(*args, **kwargs)
    return decorated_function

# --- RUTAS DE NAVEGACIÓN ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email', '').strip().lower()
        password = data.get('password')

        if email not in ADMINS_PERMITIDOS:
            error_msg = "El correo electrónico no tiene permisos de administrador."
            return jsonify({'success': False, 'message': error_msg}), 403 if request.is_json else render_template('login.html', error=error_msg)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM usuarios WHERE email = %s;", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['admin_logged_in'] = True
            session['admin_email'] = email
            return jsonify({'success': True, 'redirect': url_for('admin')}) if request.is_json else redirect(url_for('admin'))
        
        error_msg = "Contraseña incorrecta."
        return jsonify({'success': False, 'message': error_msg}), 401 if request.is_json else render_template('login.html', error=error_msg)

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    return render_template('admin.html', admin_email=session.get('admin_email'))

# --- API ENDPOINTS ---

@app.route('/api/reportes', methods=['GET'])
def get_reportes():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM reportes ORDER BY fecha_creacion DESC;")
    reportes = cur.fetchall()
    cur.close()
    conn.close()
    
    for r in reportes:
        r['fecha_creacion'] = r['fecha_creacion'].strftime("%d/%m/%Y %H:%M") if r['fecha_creacion'] else None
        r['fecha_resolucion'] = r['fecha_resolucion'].strftime("%d/%m/%Y %H:%M") if r['fecha_resolucion'] else None

    return jsonify(reportes)

@app.route('/api/reportes', methods=['POST'])
def crear_reporte():
    data = request.get_json()
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO reportes (titulo, descripcion, categoria, gravedad, latitud, longitud, imagen_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            data['titulo'],
            data['descripcion'],
            data['categoria'],
            data['gravedad'],
            float(data['latitud']),
            float(data['longitud']),
            data.get('imagen_url', '')
        ))
        nuevo_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'message': 'Reporte guardado con éxito', 'id': nuevo_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/reportes/<int:id>', methods=['PUT'])
@login_required
def modificar_reporte(id):
    data = request.get_json()
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE reportes 
            SET titulo = %s, descripcion = %s, categoria = %s, gravedad = %s
            WHERE id = %s RETURNING id;
        """, (data['titulo'], data['descripcion'], data['categoria'], data['gravedad'], id))
        updated = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        if not updated:
            return jsonify({'error': 'Reporte no encontrado'}), 404

        return jsonify({'message': 'Reporte modificado correctamente'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/reportes/<int:id>/resolver', methods=['PUT'])
@login_required
def resolver_reporte(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE reportes 
        SET estado = 'resuelto', fecha_resolucion = CURRENT_TIMESTAMP 
        WHERE id = %s RETURNING id;
    """, (id,))
    updated = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not updated:
        return jsonify({'error': 'Reporte no encontrado'}), 404

    return jsonify({'message': 'Reporte resuelto'})

@app.route('/api/reportes/<int:id>', methods=['DELETE'])
@login_required
def borrar_reporte(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM reportes WHERE id = %s RETURNING id;", (id,))
    deleted = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not deleted:
        return jsonify({'error': 'Reporte no encontrado'}), 404

    return jsonify({'message': 'Reporte borrado de PostgreSQL'})