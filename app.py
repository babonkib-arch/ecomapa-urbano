import os
import psycopg2
import psycopg2.extras
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
# (importa las demás librerías que ya uses en tu proyecto, como session, etc.)

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'  # Cambia esto por tu clave secreta de Flask

# Función para obtener la conexión a la base de datos PostgreSQL (Supabase)
def obtener_conexion():
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        # A veces Render o SQLAlchemy usan 'postgres://' pero psycopg2 exige 'postgresql://'
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        # cursor_factory=psycopg2.extras.DictCursor permite acceder a las columnas por su nombre (ej: row['descripcion'])
        conexion = psycopg2.connect(database_url, cursor_factory=psycopg2.extras.DictCursor)
    else:
        raise Exception("No se encontró la variable de entorno DATABASE_URL.")
    
    return conexion

# --- EJEMPLO DE RUTA PARA OBTENER / MOSTRAR REPORTES ---
@app.route('/')
def index():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    # Nota: psycopg2 usa %s en lugar de ? para los parámetros
    cursor.execute("SELECT * FROM reportes ORDER BY id DESC;")
    reportes = cursor.fetchall()
    
    cursor.close()
    conexion.close()
    
    return render_template('index.html', reportes=reportes)

# --- EJEMPLO DE RUTA PARA CREAR UN REPORTE ---
@app.route('/agregar', methods=['POST'])
def agregar_reporte():
    categoria = request.form.get('categoria')
    descripcion = request.form.get('descripcion')
    gravedad = request.form.get('gravedad')
    latitud = request.form.get('latitud')
    longitud = request.form.get('longitud')
    
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    # Inserción en PostgreSQL usando %s
    cursor.execute(
        """
        INSERT INTO reportes (descripcion, gravedad, latitud, longitud, estado) 
        VALUES (%s, %s, %s, %s, 'Pendiente')
        """,
        (descripcion, gravedad, latitud, longitud)
    )
    
    conexion.commit()
    cursor.close()
    conexion.close()
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)