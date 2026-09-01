import os
import sqlite3
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave-super-secreta-eco-mapa-2026'

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
DATABASE = 'database.db'

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class Usuario(UserMixin):
    def __init__(self, id, email, es_admin=False):
        self.id = id
        self.email = email
        self.es_admin = es_admin

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calcular_tiempo_transcurrido(fecha_str):
    if not fecha_str or fecha_str == 'None' or fecha_str == 'N/D':
        return "Hace tiempo"
    try:
        fecha_reporte = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')
        ahora = datetime.now()
        diferencia = ahora - fecha_reporte
        
        segundos = diferencia.total_seconds()
        minutos = int(segundos // 60)
        horas = int(minutos // 60)
        dias = int(horas // 24)
        
        if dias > 0:
            return f"Hace {dias} {'día' if dias == 1 else 'días'}"
        elif horas > 0:
            return f"Hace {horas} {'hora' if horas == 1 else 'horas'}"
        elif minutos > 0:
            return f"Hace {minutos} {'minuto' if minutos == 1 else 'minutos'}"
        else:
            return "Hace un momento"
    except Exception:
        return "Hace tiempo"

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabla de categorías
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL
        )
    ''')
    
    # Tabla de reportes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reportes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_categoria INTEGER,
            descripcion TEXT NOT NULL,
            gravedad TEXT NOT NULL,
            estado TEXT DEFAULT 'Pendiente',
            latitud REAL NOT NULL,
            longitud REAL NOT NULL,
            foto_path TEXT,
            fecha_creacion TEXT,
            FOREIGN KEY (id_categoria) REFERENCES categorias (id)
        )
    ''')
    
    cursor.execute("PRAGMA table_info(reportes)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'fecha_creacion' not in columns:
        cursor.execute("ALTER TABLE reportes ADD COLUMN fecha_creacion TEXT")
    
    fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("UPDATE reportes SET fecha_creacion = ? WHERE fecha_creacion IS NULL OR fecha_creacion = '' OR fecha_creacion = 'None'", 
                   (fecha_actual,))
    
    # Tabla de Usuarios / Admins
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            es_admin INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('SELECT COUNT(*) FROM categorias')
    if cursor.fetchone()[0] == 0:
        categorias = [
            ("Microbasural / Acumulación de residuos",),
            ("Poda indebida / Árbol en riesgo",),
            ("Vertido de aguas servidas / Contaminación",),
            ("Falta de iluminación pública",),
            ("Contaminación de aire / Humo",),
            ("Ruidos molestos / Contaminación acústica",),
            ("Animales sueltos / Plagas",)
        ]
        cursor.executemany('INSERT INTO categorias (nombre) VALUES (?)', categorias)
        
    admins_predeterminados = [
        "admin@ecomapa.com",
        "babonkib@gmail.com",
        "etchartjazmin100@gmail.com",
        "virginiasaldanaberruti@gmail.com",
        "wnores@gmail.com"
    ]
    
    pass_hash = generate_password_hash("admin123")
    
    for email_admin in admins_predeterminados:
        cursor.execute('SELECT COUNT(*) FROM usuarios WHERE email = ?', (email_admin,))
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO usuarios (email, password, es_admin) VALUES (?, ?, 1)', 
                           (email_admin, pass_hash))
        
    conn.commit()
    conn.close()

init_db()

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        return Usuario(user['id'], user['email'], bool(user['es_admin']))
    return None

# ---------------- RUTAS PÚBLICAS ----------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/reportes', methods=['GET'])
def obtener_reportes():
    conn = get_db_connection()
    reportes = conn.execute('''
        SELECT r.id, 
               COALESCE(c.nombre, 'Incidencia General') as categoria, 
               r.descripcion, r.gravedad, r.estado, r.latitud, r.longitud, r.foto_path, r.fecha_creacion
        FROM reportes r 
        LEFT JOIN categorias c ON r.id_categoria = c.id
        WHERE r.estado != 'Resuelto' OR r.estado IS NULL
        ORDER BY r.id DESC
    ''').fetchall()
    conn.close()
    
    lista_resultado = []
    for r in reportes:
        dic = dict(r)
        if not dic.get('fecha_creacion'):
            dic['fecha_creacion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        dic['tiempo_transcurrido'] = calcular_tiempo_transcurrido(dic.get('fecha_creacion'))
        lista_resultado.append(dic)
        
    return jsonify(lista_resultado)

@app.route('/api/reportes', methods=['POST'])
def crear_reporte():
    try:
        id_categoria = request.form.get('id_categoria')
        descripcion = request.form.get('descripcion')
        gravedad = request.form.get('gravedad')
        latitud = request.form.get('latitud')
        longitud = request.form.get('longitud')
        fecha_creacion = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if not id_categoria or id_categoria == 'otro':
            id_categoria = 1
            
        foto_path = None
        if 'foto' in request.files:
            file = request.files['foto']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{int(time.time())}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                foto_path = f"uploads/{filename}"

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO reportes (id_categoria, descripcion, gravedad, latitud, longitud, foto_path, fecha_creacion)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (id_categoria, descripcion, gravedad, latitud, longitud, foto_path, fecha_creacion))
        conn.commit()
        conn.close()

        return jsonify({'status': 'success', 'message': 'Reporte guardado.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ---------------- AUTENTICACIÓN Y ADMIN ----------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        user_data = conn.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user_data and check_password_hash(user_data['password'], password):
            user = Usuario(user_data['id'], user_data['email'], bool(user_data['es_admin']))
            login_user(user)
            return redirect(url_for('admin'))
        
        flash('Correo o contraseña incorrectos.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin():
    if not current_user.es_admin:
        return "Acceso denegado.", 403

    conn = get_db_connection()
    reportes = conn.execute('''
        SELECT r.id, COALESCE(c.nombre, 'Incidencia General') as categoria, 
               r.descripcion, r.gravedad, r.estado, r.latitud, r.longitud, r.foto_path, r.fecha_creacion
        FROM reportes r 
        LEFT JOIN categorias c ON r.id_categoria = c.id
        ORDER BY r.id DESC
    ''').fetchall()
    conn.close()
    
    lista_reportes = []
    for r in reportes:
        dic = dict(r)
        if not dic.get('fecha_creacion'):
            dic['fecha_creacion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        dic['tiempo_transcurrido'] = calcular_tiempo_transcurrido(dic.get('fecha_creacion'))
        lista_reportes.append(dic)
    
    return render_template('admin.html', reportes=lista_reportes, user=current_user)

@app.route('/admin/eliminar/<int:id>', methods=['POST'])
@login_required
def admin_eliminar(id):
    if not current_user.es_admin:
        return jsonify({'status': 'error', 'message': 'Acceso denegado.'}), 403
        
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM reportes WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'message': 'Incidencia resuelta correctamente.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)