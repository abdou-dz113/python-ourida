from flask import Flask, render_template, request, redirect, url_for, session, flash, g
import mysql.connector
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.secret_key = os.getenv('SECRET_KEY', 'your_default_secret_key')

# Database connection

def get_db_connection():
    if 'db' not in g or not g.db.is_connected():
        g.db = mysql.connector.connect(
            host=os.getenv('MYSQLHOST'),
            user=os.getenv('MYSQLUSER'),
            password=os.getenv('MYSQLPASSWORD'),
            database=os.getenv('MYSQLDATABASE'),
            port=int(os.getenv('MYSQLPORT', 3306))
        )
    return g.db

@app.teardown_appcontext
def close_db_connection(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/home')
def home_page():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        action = request.form.get('action')
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if action == 'login':
            cursor.execute("SELECT * FROM admins WHERE email = %s AND mot_de_passe = %s", (email, password))
            admin = cursor.fetchone()
            if admin:
                session['admin_id'] = admin['id']
                session['admin_name'] = admin['nom']
                return redirect(url_for('dashboard'))
            else:
                error = "E-mail ou mot de passe incorrect"

        elif action == 'register':
            name = request.form.get('name')
            cursor.execute("SELECT * FROM admins WHERE email = %s", (email,))
            existing = cursor.fetchone()
            if existing:
                error = "L'e-mail est déjà utilisé"
            else:
                cursor.execute("INSERT INTO admins (nom, email, mot_de_passe) VALUES (%s, %s, %s)", (name, email, password))
                conn.commit()
                cursor.execute("SELECT * FROM admins WHERE email = %s", (email,))
                new_admin = cursor.fetchone()
                session['admin_id'] = new_admin['id']
                session['admin_name'] = new_admin['nom']
                return redirect(url_for('dashboard'))

        cursor.close()
        conn.close()

    return render_template('login.html', error=error)

@app.route('/dashboard')
def dashboard():
    if 'admin_id' in session:
        return render_template('Dashbord.html', name=session['admin_name'])
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/G_Voyages')
def G_Voyages():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM voyages")
    voyages = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('G_Voyages.html', voyages=voyages)

@app.route('/add_voyage', methods=['POST'])
def add_voyage():
    destination = request.form.get('destination')
    travel_type = request.form.get('travelType')
    date_depart = request.form.get('departureDate')
    date_retour = request.form.get('returnDate')
    price = request.form.get('price')
    available_places = request.form.get('availablePlaces')
    status = request.form.get('status')
    description = request.form.get('description', '')

    travel_type = {'medicale': 'medical', 'hejj': 'hajj'}.get(travel_type, travel_type)
    status = {'active': 'actif', 'archived': 'archive'}.get(status, status)

    image_file = request.files.get('image')
    image_filename = None
    if image_file and image_file.filename:
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(image_path)
        image_filename = filename

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO voyages (destination, type, image, date_depart, date_retour, prix, places_disponibles, statut, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (destination, travel_type, image_filename, date_depart, date_retour, price, available_places, status, description))
        conn.commit()
        flash('Voyage ajouté avec succès!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erreur: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('G_Voyages'))

@app.route('/guides')
def page_guides():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM guides")
    guides = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('gGuide.html', guides=guides)

@app.route('/add_guide', methods=['POST'])
def add_guide():
    nom = request.form.get('nom')
    prenom = request.form.get('prenom')
    email = request.form.get('email')
    telephone = request.form.get('telephone')
    experience = request.form.get('experience')
    voyage = request.form.get('voyage')
    languages = ','.join(request.form.getlist('languages'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO guides (nom, prenom, email, telephone, experience, voyage, languages)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (nom, prenom, email, telephone, experience, voyage, languages))
        conn.commit()
        flash("Guide ajouté avec succès", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Erreur: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('page_guides'))
