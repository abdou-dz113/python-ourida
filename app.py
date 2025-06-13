from flask import Flask, render_template, request, redirect, url_for, session, flash, g
import mysql.connector
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import urllib.parse as urlparse

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.secret_key = os.getenv('SECRET_KEY', 'your_default_secret_key')

# Database connection

def get_db_connection():
    db_url = os.environ.get("MYSQL_URL")

    if not db_url:
        raise Exception("MYSQL_URL environment variable is not set")

    db = urlparse.urlparse(db_url)

    return mysql.connector.connect(
        host=db.hostname,
        user=db.username,
        password=db.password,
        database=db.path.lstrip("/"),
        port=db.port or 3306
    )

@app.teardown_appcontext
def close_db_connection(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.route('/G_Transport')
def G_Transport():
    return render_template('G_Transport.html')

@app.route('/vip')
def vip():
    return render_template('Vip.html')
@app.route('/contact')
def contact():
    return render_template('Contact.html')
@app.route('/G_Factures')
def G_Factures():
    return render_template('G_Factures.html')
@app.route('/Hotels')
def Hotels():
    return render_template('Hotels.html')
@app.route('/حجز')
def booking():
    return render_template('حجز.html')

@app.route('/G_Reservations')
def G_Reservations():
    return render_template('G_Réservations.html')
@app.route('/G_Offres')
def G_Offres():
    return render_template('G_Offres.html')
@app.route('/G_Clients')
def G_Clients():
    return render_template('G_Clients.html')
@app.route('/G_Messages')
def G_Messages():
    return render_template('gMsg.html')

@app.route('/medical-trips')
def medical_trips():
    return render_template('Medical Trips.html')
@app.route('/national-trips')
def national_trips():
    return render_template('National Trips.html')
@app.route('/international-trips')
def international_trips():
    return render_template('International trips.html')  
@app.route('/omra-trips')
def omra_trips():
    return render_template('haj.html')
@app.route('/gallery')  
def gallery():
    return render_template('Gallery.html')
@app.route('/offers')
def offers():
    return render_template('offers.html')





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

