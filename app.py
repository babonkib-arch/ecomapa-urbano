import os
import sqlite3
import time
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
            FOREIGN KEY (id_categoria) REFERENCES categorias (id)
        )
    ''')
    
    # Tabla de Usuarios / Admins
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            es_admin INTEGER DEFAULT 0
        )
    ''')
    
    # Categorías iniciales
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
        
    # Administradores Predeterminados
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

# Al resolver una incidencia, se excluye del mapa público
@app.route('/api/reportes', methods=['GET'])
def obtener_reportes():
    conn = get_db_connection()
    reportes = conn.execute('''
        SELECT r.id, 
               COALESCE(c.nombre, 'Incidencia General') as categoria, 
               r.descripcion, r.gravedad, r.estado, r.latitud, r.longitud, r.foto_path 
        FROM reportes r 
        LEFT JOIN categorias c ON r.id_categoria = c.id
        WHERE r.estado != 'Resuelto' OR r.estado IS NULL
        ORDER BY r.id DESC
    ''').fetchall()
    conn.close()
    return jsonify([dict(r) for r in reportes])

@app.route('/api/reportes', methods=['POST'])
def crear_reporte():
    try:
        id_categoria = request.form.get('id_categoria')
        descripcion = request.form.get('descripcion')
        gravedad = request.form.get('gravedad')
        latitud = request.form.get('latitud')
        longitud = request.form.get('longitud')
        
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
            INSERT INTO reportes (id_categoria, descripcion, gravedad, latitud, longitud, foto_path)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (id_categoria, descripcion, gravedad, latitud, longitud, foto_path))
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
               r.descripcion, r.gravedad, r.estado, r.latitud, r.longitud, r.foto_path 
        FROM reportes r 
        LEFT JOIN categorias c ON r.id_categoria = c.id
        ORDER BY r.id DESC
    ''').fetchall()
    conn.close()
    
    return render_template('admin.html', reportes=reportes, user=current_user)

@app.route('/admin/resolver/<int:id_reporte>', methods=['POST'])
@login_required
def resolver_reporte(id_reporte):
    conn = get_db_connection()
    conn.execute('UPDATE reportes SET estado = "Resuelto" WHERE id = ?', (id_reporte,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)