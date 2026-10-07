import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables de entorno (.env)
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "eco_mapa_fray_bentos_secret_key_2026")

# Configuración de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Error al inicializar Supabase: {e}")

# Configuración Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id, email):
        self.id = id
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    # En un entorno real se verifica la sesión del usuario.
    return User(user_id, "admin@fraybentos.gub.uy")

# --- RUTAS DE VISTAS ---

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Validación simple o con Supabase Auth
        if email and password:
            user = User(id="1", email=email)
            login_user(user)
            return redirect(url_for("admin"))
        
        return render_template("login.html", error="Credenciales inválidas")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/admin")
@login_required
def admin():
    return render_template("admin.html")

# --- ENDPOINTS API PARA REPORTES ---

@app.route("/api/reportes", methods=["GET"])
def get_reportes():
    if not supabase:
        return jsonify([]), 200
    try:
        res = supabase.table("reportes").select("*").order("created_at", desc=True).execute()
        return jsonify(res.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/reportes/<reporte_id>", methods=["GET"])
def get_reporte_by_id(reporte_id):
    if not supabase:
        return jsonify({"error": "Sin conexión"}), 500
    try:
        res = supabase.table("reportes").select("*").eq("id", reporte_id).single().execute()
        return jsonify(res.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@app.route("/api/reportes", methods=["POST"])
def create_reporte():
    if not supabase:
        return jsonify({"error": "Sin conexión a base de datos"}), 500
    try:
        data = request.json
        res = supabase.table("reportes").insert(data).execute()
        return jsonify(res.data), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/reportes/<reporte_id>", methods=["PUT"])
@login_required
def update_reporte(reporte_id):
    if not supabase:
        return jsonify({"error": "Sin conexión a base de datos"}), 500
    try:
        data = request.json
        res = supabase.table("reportes").update(data).eq("id", reporte_id).execute()
        return jsonify(res.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/reportes/<reporte_id>", methods=["DELETE"])
@login_required
def delete_reporte(reporte_id):
    if not supabase:
        return jsonify({"error": "Sin conexión a base de datos"}), 500
    try:
        res = supabase.table("reportes").delete().eq("id", reporte_id).execute()
        return jsonify({"message": "Eliminado exitosamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)