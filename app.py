from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import json
import uuid
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

cred = credentials.Certificate('tai-khamyang-app-firebase-adminsdk-fbsvc-f89b5718fc.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

app.secret_key = 'tai_khamyang_secret_key_2025'  # Change this in production
app.config['UPLOAD_FOLDER'] = 'static/audio'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)





# Firebase initialization
def init_firestore():
    try:
        # Check if admin exists, if not create default
        admin_ref = db.collection('admin').document('default_admin')
        if not admin_ref.get().exists:
            hashed_password = generate_password_hash('admin123')
            admin_ref.set({
                'username': 'admin',
                'password': hashed_password
            })
            print("Default admin created")

        # Add sample words if collection is empty
        words_ref = db.collection('words')
        words_docs = list(words_ref.limit(1).stream())
        if len(words_docs) == 0:
            sample_words = [ ]
            for word in sample_words:
                words_ref.add(word)
            print("Sample words added")

        # Add sample songs if collection is empty
        songs_ref = db.collection('songs')
        songs_docs = list(songs_ref.limit(1).stream())
        if len(songs_docs) == 0:
            sample_songs = [ ]
            for song in sample_songs:
                songs_ref.add(song)
            print("Sample songs added")
        # Add sample sellers if collection is empty
        sellers_ref = db.collection('sellers')
        sellers_docs = list(sellers_ref.limit(1).stream())
        if len(sellers_docs) == 0:
            sample_seller = {
                'id': str(uuid.uuid4()),
                'business_name': 'traditional Shop',
                'email': 'khamyang@gmail.com',
                'password': generate_password_hash('khamyang123'),
                'phone': '+919876543210',
                'whatsapp': '919876543210',
                'address': 'Demo Address',
                'business_type': 'retail',
                'created_at': datetime.now(),
                'status': 'active'
            }
            sellers_ref.document(sample_seller['id']).set(sample_seller)
            print("Sample seller added")

            # Add sample products if collection is empty
            products_ref = db.collection('products')
            products_docs = list(products_ref.limit(1).stream())
            if len(products_docs) == 0:
                print("Sample products initialized")

    except Exception as e:
        print(f"Error initializing Firestore: {e}")


# Routes
@app.route('/')
def home():
    if 'user_id' in session:  # Check if user is logged in
        return render_template('index.html')  # Show main index for logged-in users
    else:
        return render_template('indexx.html')  # Show landing page for non-logged-in users


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))  # redirect to indexx.html
    return render_template('index.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out')
    return redirect(url_for('home'))  # back to indexx.html


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        password = request.form.get('password')

        # Validation
        if not all([name, phone, address, password]):
            flash('Please fill all fields')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)

        try:
            # Check if phone already exists
            users_ref = db.collection('users')
            existing_user = users_ref.where('phone', '==', phone).limit(1).stream()
            if len(list(existing_user)) > 0:
                flash('Phone number already registered')
                return redirect(url_for('register'))

            # Add new user
            user_ref = users_ref.add({
                'name': name,
                'phone': phone,
                'address': address,
                'password': hashed_password,
                'registered_at': firestore.SERVER_TIMESTAMP
            })

            # Auto login after registration
            session['user_logged_in'] = True
            session['user_name'] = name
            session['user_id'] = user_ref[1].id

            return redirect(url_for('dictionary'))
        except Exception as e:
            flash('Registration failed. Please try again.')
            print(f"Registration error: {e}")
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')

        try:
            users_ref = db.collection('users')
            user_docs = users_ref.where('phone', '==', phone).limit(1).stream()
            user_doc = None

            for doc in user_docs:
                user_doc = doc
                break

            if user_doc and check_password_hash(user_doc.to_dict()['password'], password):
                session['user_id'] = user_doc.id
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid credentials')
                return redirect(url_for('login'))
        except Exception as e:
            flash('Login failed. Please try again.')
            print(f"Login error: {e}")
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/dictionary')
def dictionary():
    return render_template('dictionary.html')


@app.route('/songs')
def songs():
    return render_template('songs.html')


@app.route('/shopnow')
def shop():
    return render_template('shop.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/admin')
def admin():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    return render_template('admin.html')


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            admin_ref = db.collection('admin').document('default_admin')
            admin_doc = admin_ref.get()

            if admin_doc.exists:
                admin_data = admin_doc.to_dict()
                if admin_data['username'] == username and check_password_hash(admin_data['password'], password):
                    session['admin_logged_in'] = True
                    return redirect(url_for('admin'))
                else:
                    flash('Invalid credentials')
            else:
                flash('Admin not found')
        except Exception as e:
            flash('Login failed. Please try again.')
            print(f"Admin login error: {e}")

    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('home'))


# ============= SHOP ROUTES =============

@app.route('/api/seller/register', methods=['POST'])
def seller_register():
    try:
        data = request.get_json()

        # Check if a seller with this email already exists
        sellers_ref = db.collection('sellers')
        existing_sellers = list(sellers_ref.where('email', '==', data['email']).stream())

        if existing_sellers:
            return jsonify({'success': False, 'message': 'Seller with this email already exists'})

        # Create the new seller document using data from the form
        # This now correctly matches the fields sent from your JavaScript
        seller_data = {
            'id': str(uuid.uuid4()),
            'full_name': data['fullName'],  # From the "Full Name" field
            'business_name': data['shopName'],  # From the "Shop Name" field
            'email': data['email'],
            'password': generate_password_hash(data['password']),  # Securely hash the password
            'phone': data['phone'],
            'whatsapp': data['whatsapp'],
            'created_at': datetime.now(),
            'status': 'active'
        }

        # Add the new seller data to the 'sellers' collection in Firestore
        db.collection('sellers').document(seller_data['id']).set(seller_data)

        return jsonify({'success': True, 'message': 'Seller registered successfully'})

    except Exception as e:
        # Return an error if something goes wrong
        print(f"Seller registration error: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/seller/login', methods=['POST'])
def seller_login():
    try:
        data = request.get_json()

        # Find the seller in the database by their email address
        sellers_ref = db.collection('sellers')
        sellers = list(sellers_ref.where('email', '==', data['email']).stream())

        # If no seller is found with that email, return an error
        if not sellers:
            return jsonify({'success': False, 'message': 'Invalid email or password'})

        seller_doc = sellers[0]
        seller = seller_doc.to_dict()
        seller['id'] = seller_doc.id  # Get the document ID

        # Check if the provided password matches the stored hashed password
        if check_password_hash(seller['password'], data['password']):
            # If login is successful, store seller info in the session
            session['seller_id'] = seller['id']
            session['seller_name'] = seller['business_name']

            # Return success and seller details to the frontend
            return jsonify({'success': True, 'seller': {
                'id': seller['id'],
                'business_name': seller['business_name'],
                'email': seller['email']
            }})
        else:
            # If passwords do not match, return an error
            return jsonify({'success': False, 'message': 'Invalid email or password'})

    except Exception as e:
        print(f"Seller login error: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/seller/logout', methods=['POST'])
def seller_logout():
    session.pop('seller_id', None)
    session.pop('seller_name', None)
    return jsonify({'success': True})


@app.route('/api/products/add', methods=['POST'])
def add_product():
    try:
        if 'seller_id' not in session:
            return jsonify({'success': False, 'message': 'Please login first'})

        data = request.get_json()

        product_data = {
            'id': str(uuid.uuid4()),
            'seller_id': session['seller_id'],
            'name': data['name'],
            'description': data['description'],
            'category': data['category'],
            'price': float(data['price']),
            'original_price': float(data.get('originalPrice', data['price'])),
            'sizes': data.get('sizes', []),
            'images': data.get('images', []),
            'stock_quantity': int(data.get('stockQuantity', 0)),
            'status': 'active',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }

        # Add to Firestore
        db.collection('products').document(product_data['id']).set(product_data)

        return jsonify({'success': True, 'message': 'Product added successfully'})

    except Exception as e:
        print(f"Add product error: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        products_ref = db.collection('products')
        products = list(products_ref.where('status', '==', 'active').stream())

        product_list = []
        for product_doc in products:
            product_data = product_doc.to_dict()
            product_data['id'] = product_doc.id

            # Get seller info
            seller_doc = db.collection('sellers').document(product_data['seller_id']).get()
            if seller_doc.exists:
                seller_data = seller_doc.to_dict()
                product_data['seller_info'] = {
                    'business_name': seller_data['business_name'],
                    'whatsapp': seller_data['whatsapp'],
                    'phone': seller_data['phone']
                }

            product_list.append(product_data)

        return jsonify({'success': True, 'products': product_list})

    except Exception as e:
        print(f"Get products error: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/seller/products', methods=['GET'])
def get_seller_products():
    try:
        if 'seller_id' not in session:
            return jsonify({'success': False, 'message': 'Please login first'})

        products_ref = db.collection('products')
        products = list(products_ref.where('seller_id', '==', session['seller_id']).stream())

        product_list = []
        for product_doc in products:
            product_data = product_doc.to_dict()
            product_data['id'] = product_doc.id
            product_list.append(product_data)

        return jsonify({'success': True, 'products': product_list})

    except Exception as e:
        print(f"Get seller products error: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        if 'seller_id' not in session:
            return jsonify({'success': False, 'message': 'Please login first'})

        # Check if product belongs to seller
        product_doc = db.collection('products').document(product_id).get()
        if not product_doc.exists:
            return jsonify({'success': False, 'message': 'Product not found'})

        product_data = product_doc.to_dict()
        if product_data['seller_id'] != session['seller_id']:
            return jsonify({'success': False, 'message': 'Unauthorized'})

        # Delete product
        db.collection('products').document(product_id).delete()

        return jsonify({'success': True, 'message': 'Product deleted successfully'})

    except Exception as e:
        print(f"Delete product error: {e}")
        return jsonify({'success': False, 'message': str(e)})


# API Routes
@app.route('/api/words')
def get_words():
    search = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'tai_khamyang')

    try:
        words_ref = db.collection('words')
        words = []

        for doc in words_ref.stream():
            word_data = doc.to_dict()
            word_data['id'] = doc.id

            # Client-side search filtering
            if search:
                search_lower = search.lower()
                if (search_lower in word_data.get('tai_khamyang', '').lower() or
                        search_lower in word_data.get('english', '').lower() or
                        search_lower in word_data.get('assamese', '').lower()):
                    words.append(word_data)
            else:
                words.append(word_data)

        # Client-side sorting
        if sort_by in ['tai_khamyang', 'english', 'assamese']:
            words.sort(key=lambda x: x.get(sort_by, '').lower())

        return jsonify(words)
    except Exception as e:
        print(f"Error getting words: {e}")
        return jsonify([])


@app.route('/api/songs')
def get_songs():
    search = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'title')

    try:
        songs_ref = db.collection('songs')
        songs = []

        for doc in songs_ref.stream():
            song_data = doc.to_dict()
            song_data['id'] = doc.id

            # Client-side search filtering
            if search:
                search_lower = search.lower()
                if (search_lower in song_data.get('title', '').lower() or
                        search_lower in song_data.get('description', '').lower()):
                    songs.append(song_data)
            else:
                songs.append(song_data)

        # Client-side sorting
        if sort_by in ['title', 'description']:
            songs.sort(key=lambda x: x.get(sort_by, '').lower())

        return jsonify(songs)
    except Exception as e:
        print(f"Error getting songs: {e}")
        return jsonify([])


@app.route('/api/words', methods=['POST'])
def add_word():
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get data from form or JSON
        if request.is_json:
            data = request.get_json()
            tai_khamyang = data.get('tai_khamyang')
            english = data.get('english')
            assamese = data.get('assamese')
            audio_path = None
        else:
            tai_khamyang = request.form.get('tai_khamyang')
            english = request.form.get('english')
            assamese = request.form.get('assamese')

            audio_file = request.files.get('audio')
            audio_path = None
            if audio_file:
                filename = secure_filename(audio_file.filename)
                audio_path = filename
                audio_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        word_data = {
            'tai_khamyang': tai_khamyang,
            'english': english,
            'assamese': assamese
        }

        if audio_path:
            word_data['audio_path'] = audio_path

        words_ref = db.collection('words')
        doc_ref = words_ref.add(word_data)

        return jsonify({'success': True, 'id': doc_ref[1].id})

    except Exception as e:
        print(f"Error adding word: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/words/<word_id>', methods=['PUT'])
def update_word(word_id):
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            tai_khamyang = data.get('tai_khamyang')
            english = data.get('english')
            assamese = data.get('assamese')
            audio_path = None
        else:
            tai_khamyang = request.form.get('tai_khamyang')
            english = request.form.get('english')
            assamese = request.form.get('assamese')

            # Handle file upload if present
            audio_file = request.files.get('audio')
            audio_path = None
            if audio_file:
                filename = secure_filename(audio_file.filename)
                audio_path = filename
                audio_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Validate required fields
        if not all([tai_khamyang, english, assamese]):
            return jsonify({'error': 'Missing required fields'}), 400

        word_data = {
            'tai_khamyang': tai_khamyang,
            'english': english,
            'assamese': assamese
        }

        if audio_path:
            word_data['audio_path'] = audio_path

        word_ref = db.collection('words').document(word_id)
        word_ref.update(word_data)

        return jsonify({'message': 'Word updated successfully'})

    except Exception as e:
        print(f'Error in update_word: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/words/<word_id>', methods=['DELETE'])
def delete_word(word_id):
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        word_ref = db.collection('words').document(word_id)
        word_ref.delete()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/songs', methods=['POST'])
def add_song():
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get data from form or JSON
        if request.is_json:
            data = request.get_json()
            title = data.get('title')
            description = data.get('description')
            file_path = None
        else:
            title = request.form.get('title')
            description = request.form.get('description')

            # Handle audio file upload
            audio_file = request.files.get('audio')
            file_path = None
            if audio_file:
                filename = secure_filename(audio_file.filename)
                file_path = filename
                audio_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        song_data = {
            'title': title,
            'description': description
        }

        if file_path:
            song_data['file_path'] = file_path

        songs_ref = db.collection('songs')
        doc_ref = songs_ref.add(song_data)

        return jsonify({'success': True, 'id': doc_ref[1].id})

    except Exception as e:
        print(f"Error adding song: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/songs/<song_id>', methods=['PUT'])
def update_song(song_id):
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            title = data.get('title')
            description = data.get('description')
            file_path = None
        else:
            title = request.form.get('title')
            description = request.form.get('description')

            # Handle file upload if present
            audio_file = request.files.get('audio')
            file_path = None
            if audio_file:
                filename = secure_filename(audio_file.filename)
                file_path = filename
                audio_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Validate required fields
        if not title:
            return jsonify({'error': 'Title is required'}), 400

        song_data = {
            'title': title,
            'description': description
        }

        if file_path:
            song_data['file_path'] = file_path

        song_ref = db.collection('songs').document(song_id)
        song_ref.update(song_data)

        return jsonify({'message': 'Song updated successfully'})

    except Exception as e:
        print(f'Error in update_song: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/songs/<song_id>', methods=['DELETE'])
def delete_song(song_id):
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        song_ref = db.collection('songs').document(song_id)
        song_ref.delete()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    init_firestore()
    app.run(debug=True, host='0.0.0.0', port=5000)