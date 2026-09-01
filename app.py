import os
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import psycopg2.extras
from supabase import create_client, Client

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave-super-secreta-eco-mapa-2026'

# --- CONFIGURACIÓN DE SUPABASE STORAGE ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase_cliente = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase_cliente = create_client(SUPABASE_URL, SUPABASE_KEY)
# ----------------------------------------

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
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(database_url, cursor_factory=psycopg2.extras.DictCursor)
    else:
        raise Exception("No se encontró la variable de entorno DATABASE_URL.")
    return conn

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
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
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL
        )
    ''')
    
    # Tabla de reportes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reportes (
            id SERIAL PRIMARY KEY,
            id_categoria INTEGER,
            descripcion TEXT NOT NULL,
            gravedad TEXT NOT NULL,
            estado TEXT DEFAULT 'Pendiente',
            latitud DOUBLE PRECISION NOT NULL,
            longitud DOUBLE PRECISION NOT NULL,
            foto_path TEXT,
            fecha_creacion TEXT,
            FOREIGN KEY (id_categoria) REFERENCES categorias (id)
        )
    ''')
    
    # Tabla de Usuarios / Admins
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            es_admin INTEGER DEFAULT 0
        )
    ''')
    
    # Verificar e insertar categorías predeterminadas
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
        cursor.executemany('INSERT INTO categorias (nombre) VALUES (%s)', categorias)
        
    admins_predeterminados = [
        "admin@ecomapa.com",
        "babonkib@gmail.com",
        "etchartjazmin100@gmail.com",
        "virginiasaldanaberruti@gmail.com",
        "wnores@gmail.com"
    ]
    
    pass_hash = generate_password_hash("admin123")
    
    for email_admin in admins_predeterminados:
        cursor.execute('SELECT COUNT(*) FROM usuarios WHERE email = %s', (email_admin,))
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO usuarios (email, password, es_admin) VALUES (%s, %s, 1)', 
                           (email_admin, pass_hash))
        
    conn.commit()
    cursor.close()
    conn.close()

init_db()

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    cursor.close()
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
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.id, 
               COALESCE(c.nombre, 'Incidencia General') as categoria, 
               r.descripcion, r.gravedad, r.estado, r.latitud, r.longitud, r.foto_path, r.fecha_creacion
        FROM reportes r 
        LEFT JOIN categorias c ON r.id_categoria = c.id
        WHERE r.estado != 'Resuelto' OR r.estado IS NULL
        ORDER BY r.id DESC
    ''')
    reportes = cursor.fetchall()
    cursor.close()
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
                unique_filename = f"{int(time.time())}_{filename}"
                
                # Sube la foto directamente a Supabase Storage (Bucket: "fotos")
                if supabase_cliente:
                    file_bytes = file.read()
                    supabase_cliente.storage.from_("fotos").upload(
                        path=unique_filename,
                        file=file_bytes,
                        file_options={"content-type": file.content_type}
                    )
                    # Guarda el enlace público completo en la base de datos
                    foto_path = supabase_cliente.storage.from_("fotos").get_public_url(unique_filename)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reportes (id_categoria, descripcion, gravedad, latitud, longitud, foto_path, fecha_creacion)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (id_categoria, descripcion, gravedad, latitud, longitud, foto_path, fecha_creacion))
        conn.commit()
        cursor.close()
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
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE email = %s', (email,))
        user_data = cursor.fetchone()
        cursor.close()
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
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.id, COALESCE(c.nombre, 'Incidencia General') as categoria, 
               r.descripcion, r.gravedad, r.estado, r.latitud, r.longitud, r.foto_path, r.fecha_creacion
        FROM reportes r 
        LEFT JOIN categorias c ON r.id_categoria = c.id
        ORDER BY r.id DESC
    ''')
    reportes = cursor.fetchall()
    cursor.close()
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
        cursor = conn.cursor()
        
        # Elimina la foto de Supabase Storage para liberar espacio al resolver
        if supabase_cliente:
            cursor.execute('SELECT foto_path FROM reportes WHERE id = %s', (id,))
            reporte = cursor.fetchone()
            
            if reporte and reporte['foto_path']:
                foto_url = reporte['foto_path']
                filename_to_delete = foto_url.split('/')[-1]
                try:
                    supabase_cliente.storage.from_("fotos").remove([filename_to_delete])
                except Exception as error_storage:
                    print("Error borrando foto en Supabase:", error_storage)
        
        # Borra el registro de la base de datos
        cursor.execute('DELETE FROM reportes WHERE id = %s', (id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Incidencia resuelta y foto eliminada correctamente.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)