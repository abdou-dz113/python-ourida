from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import urllib.parse as urlparse
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from flask import Flask, request, jsonify


app = Flask(__name__)
# Load MYSQL_URL from environment variables
db = urlparse.urlparse(os.environ['MYSQL_URL'])


app.config.update({
    'MYSQL_HOST': db.hostname,
    'MYSQL_USER': db.username,
    'MYSQL_PASSWORD': db.password,
    'MYSQL_DB': db.path.lstrip('/'),
    'MYSQL_PORT': db.port or 3306,
})

mysql = MySQL(app)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.secret_key = 'your_secret_key'  # مفتاح الجلسة

def get_db_connection():
    if 'db' not in g or not g.db.is_connected():
        g.db = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            port=int(os.getenv('DB_PORT', 3306))
        )
    return g.db

@app.route('/')
def home():
    return render_template(url_for('login'))
@app.route('/home')
def home_page():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        action = request.form.get('action')  # login أو register
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
                cursor.close()
                conn.close()
                return redirect(url_for('dashboard'))
            else:
                error = "E-mail ou mot de passe incorrect"

        elif action == 'register':
            name = request.form.get('name')
            if not (name and email and password):
                error = "Veuillez remplir tous les champs."
            else:
                cursor.execute("SELECT * FROM admins WHERE email = %s", (email,))
                existing = cursor.fetchone()
                if existing:
                    error = "L'e-mail est déjà utilisé"
                else:
                    cursor.execute("INSERT INTO admins (nom, email, mot_de_passe) VALUES (%s, %s, %s)", (name, email, password))
                    conn.commit()  # حفظ التغييرات
                    cursor.execute("SELECT * FROM admins WHERE email = %s", (email,))
                    new_admin = cursor.fetchone()
                    session['admin_id'] = new_admin['id']
                    session['admin_name'] = new_admin['nom']
                    cursor.close()
                    conn.close()
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
    total_places = request.form.get('totalPlaces')
    available_places = request.form.get('availablePlaces')
    status = request.form.get('status')
    description = request.form.get('description', '')

    # تعديل القيم لتتناسب مع الجدول
    if travel_type == 'medicale':
        travel_type = 'medical'
    elif travel_type == 'hejj':
        travel_type = 'hajj'

    if status == 'active':
        status = 'actif'
    elif status == 'archived':
        status = 'archive'

    image_file = request.files.get('image')
    image_filename = None
    if image_file and image_file.filename != '':
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(image_path)
        image_filename = filename

    conn = get_db_connection()
    cursor = conn.cursor()

    sql = """
    INSERT INTO voyages 
    (destination, type, image, date_depart, date_retour, prix, places_disponibles, statut, description) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    try:
        cursor.execute(sql, (
            destination,
            travel_type,
            image_filename,
            date_depart,
            date_retour,
            price,
            available_places,
            status,
            description
        ))
        conn.commit()
        flash('Voyage ajouté avec succès!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erreur lors de l\'ajout du voyage: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()

    # بعد الإضافة يعيد توجيه لعرض صفحة الرحلات مع البيانات المحدثة
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
    print("Add guide called")
    nom = request.form.get('nom')
    prenom = request.form.get('prenom')
    email = request.form.get('email')
    telephone = request.form.get('telephone')
    experience = request.form.get('experience')
    voyage = request.form.get('voyage')
    languages = request.form.getlist('languages')
    languages_str = ','.join(languages) if languages else ''

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO guides (nom, prenom, email, telephone, experience, voyage, languages)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (nom, prenom, email, telephone, experience, voyage, languages_str))
        conn.commit()
        flash("Guide ajouté avec succès", "success")
    except Exception as e:
        conn.rollback()
        print(f"Error inserting guide: {e}")  # لطباعة الخطأ في الكونسول
        flash(f"Erreur lors de l'ajout du guide: {e}", "danger")
    finally:
        cursor.close()
        conn.close()
      

    return redirect(url_for('page_guides'))
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


@app.route('/add-transport', methods=['POST'])
def add_transport():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        type_transport = request.form['typeTransport']
        societe = request.form['nomSociete']
        marque = request.form.get('marque')
        matricule = request.form['matricule']
        prix = request.form['prix']
        chauffeur_nom = request.form['chauffeur']
        chauffeur_telephone = request.form['telChauffeur']
        chauffeur_permis = request.form['numPermis']
        capacite = request.form['capacite']
        
        voyage_id = None

        sql = """
        INSERT INTO transports (
            type, societe, marque, matricule, prix, 
            chauffeur_nom, chauffeur_telephone, chauffeur_permis, 
            voyage_id, capacite
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            type_transport, societe, marque, matricule, prix,
            chauffeur_nom, chauffeur_telephone, chauffeur_permis,
            voyage_id, capacite
        )

        # تأكدي أن cursor معرف في أعلى الملف مثل:
        # cursor = db.cursor()
        cursor.execute(sql, values)
        conn.commit()
        cursor.close()
        conn.close()


        flash("Transport ajouté avec succès !")
    except mysql.connector.Error as err:
        flash(f"Erreur lors de l'ajout: {err}")
    return redirect('/G_Transport')

@app.route('/add-hotel', methods=['POST'])
def add_hotel():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        nom = request.form['hotel-name']
        ville = request.form['hotel-city']
        pays = request.form['hotel-country']
        nb_etoiles = request.form.get('rating', None)
        voyage_id = None  # غيّري هذا إذا كنتِ تربطين الفندق برحلة

        sql = """
        INSERT INTO hotels (nom, ville, pays, nb_etoiles, voyage_id)
        VALUES (%s, %s, %s, %s, %s)
        """
        values = (nom, ville, pays, nb_etoiles, voyage_id)
        cursor.execute(sql, values)
        conn.commit()
        flash("✅ تمت إضافة الفندق بنجاح!")
    except Exception as e:
        conn.rollback()
        flash(f"❌ خطأ أثناء الإضافة: {str(e)}")
    finally:
        cursor.close()
        conn.close()
    return redirect('Hotels') 

@app.route('/ajouter-offre', methods=['GET', 'POST'])
def ajouter_offre():
    if request.method == 'POST':
        try:
            # جلب البيانات من الفورم
            destination = request.form['destination']
            travel_type = request.form['travelType']
            departure_date = request.form['departureDate']
            return_date = request.form['returnDate']
            price = request.form['price']
            reduction = request.form['reduction']
            total_places = request.form['totalPlaces']
            available_places = request.form['availablePlaces']
            status = request.form['status']

            # ✅ طباعة البيانات للتأكد أنها تصل
            print("Form data received:")
            print("Destination:", destination)
            print("Type:", travel_type)
            print("Date départ:", departure_date)
            print("Date retour:", return_date)
            print("Prix:", price)
            print("Réduction:", reduction)
            print("Total places:", total_places)
            print("Available places:", available_places)
            print("Status:", status)

            # معالجة الصورة
            image = request.files['image']
            image_filename = None
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(image_path)
                image_filename = f"/{image_path}"

            # الاتصال بقاعدة البيانات
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
            INSERT INTO offres (
                destination, travel_type, departure_date, return_date,
                price, reduction, total_places, available_places,
                status, image
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                destination, travel_type, departure_date, return_date,
                price, reduction, total_places, available_places,
                status, image_filename
            )

            cursor.execute(query, values)
            conn.commit()
            cursor.close()
            conn.close()

            flash("Offre ajoutée avec succès!", "success")
            return redirect(url_for('page_d_offres'))

        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Erreur: {str(e)}"
    
    # عند الوصول للرابط GET
    return render_template('G_Offres.html')

    
   
 









if __name__ == '__main__':
    app.run(debug=True)
else:
    app.run()



