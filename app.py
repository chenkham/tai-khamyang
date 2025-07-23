from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import json

app = Flask(__name__)
app.secret_key = 'tai_khamyang_secret_key_2024'  # Change this in production
app.config['UPLOAD_FOLDER'] = 'static/audio'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# Database initialization
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()


    #registration table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               name TEXT NOT NULL,
               phone TEXT UNIQUE NOT NULL,
               address TEXT NOT NULL,
               password TEXT NOT NULL,
               registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
           )''')

    # Words table
    c.execute('''CREATE TABLE IF NOT EXISTS words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tai_khamyang TEXT NOT NULL,
        english TEXT NOT NULL,
        assamese TEXT NOT NULL,
        audio_path TEXT
    )''')

    # Songs table
    c.execute('''CREATE TABLE IF NOT EXISTS songs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        file_path TEXT
    )''')

    # Admin table
    c.execute('''CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')

    # Check if admin exists, if not create default
    c.execute('SELECT * FROM admin WHERE username = ?', ('admin',))
    if not c.fetchone():
        hashed_password = generate_password_hash('admin123')
        c.execute('INSERT INTO admin (username, password) VALUES (?, ?)', ('admin', hashed_password))

    # Add sample data if tables are empty
    c.execute('SELECT COUNT(*) FROM words')
    if c.fetchone()[0] == 0:
        sample_words = [
            ('ကမ်းယန်း', 'Khamyang', 'খামইয়াং'),
            ('မန်း', 'Water', 'পানী'),
            ('ဖါး', 'Sky', 'আকাশ'),
            ('ကုမ်း', 'Child', 'শিশু'),
            ('မိတ်', 'Friend', 'বন্ধু'),
            ('ပြန်း', 'House', 'ঘৰ'),
            ('လမ်း', 'Road', 'ৰাস্তা'),
            ('နမ်း', 'Name', 'নাম')
        ]
        c.executemany('INSERT INTO words (tai_khamyang, english, assamese) VALUES (?, ?, ?)', sample_words)

    c.execute('SELECT COUNT(*) FROM songs')
    if c.fetchone()[0] == 0:
        sample_songs = [
            ('Traditional Welcome Song', 'A beautiful welcome song sung during festivals'),
            ('Harvest Festival Song', 'Song celebrating the harvest season'),
            ('River Song', 'A melodious song about the flowing river')
        ]
        c.executemany('INSERT INTO songs (title, description) VALUES (?, ?)', sample_songs)

    conn.commit()
    conn.close()


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

        # ✅ Validation
        if not all([name, phone, address, password]):
            flash('Please fill all fields')
            return redirect(url_for('register'))

        password = request.form.get('password')
        hashed_password = generate_password_hash(password)

        # Save name, phone, address, hashed_password into DB

        try:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute('INSERT INTO users (name, phone, address, password) VALUES (?, ?, ?, ?)',
                      (name, phone, address, hashed_password))
            conn.commit()

            # ✅ Auto login after registration
            session['user_logged_in'] = True
            session['user_name'] = name
            session['user_id'] = c.lastrowid

            conn.close()
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

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT id, password FROM users WHERE phone = ?', (phone,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
            return redirect(url_for('login'))

    return render_template('login.html')


# @app.route('/')
# def home():
#     # Check if user is registered (only if not admin)
#     if 'admin_logged_in' not in session and not session.get('user_registered'):
#         return redirect(url_for('register'))
#     return render_template('index.html')


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

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT password FROM admin WHERE username = ?', (username,))
        result = c.fetchone()
        conn.close()

        if result and check_password_hash(result[0], password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            flash('Invalid credentials')

    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('home'))


# API Routes
@app.route('/api/words')
def get_words():
    search = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'tai_khamyang')  # Default sort by Tai-Khamyang

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Define valid sort columns to prevent SQL injection
    valid_sort_columns = ['tai_khamyang', 'english', 'assamese']
    if sort_by not in valid_sort_columns:
        sort_by = 'tai_khamyang'

    if search:
        query = f'''SELECT * FROM words WHERE 
                   tai_khamyang LIKE ? OR 
                   english LIKE ? OR 
                   assamese LIKE ?
                   ORDER BY {sort_by} COLLATE NOCASE'''
        c.execute(query, (f'%{search}%', f'%{search}%', f'%{search}%'))
    else:
        query = f'SELECT * FROM words ORDER BY {sort_by} COLLATE NOCASE'
        c.execute(query)

    words = []
    for row in c.fetchall():
        words.append({
            'id': row[0],
            'tai_khamyang': row[1],
            'english': row[2],
            'assamese': row[3],
            'audio_path': row[4]
        })

    conn.close()
    return jsonify(words)

@app.route('/api/songs')
def get_songs():
    search = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'title')  # Default sort by title

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Define valid sort columns to prevent SQL injection
    valid_sort_columns = ['title', 'description']
    if sort_by not in valid_sort_columns:
        sort_by = 'title'

    if search:
        query = f'''SELECT * FROM songs WHERE 
                   title LIKE ? OR 
                   description LIKE ?
                   ORDER BY {sort_by} COLLATE NOCASE'''
        c.execute(query, (f'%{search}%', f'%{search}%'))
    else:
        query = f'SELECT * FROM songs ORDER BY {sort_by} COLLATE NOCASE'
        c.execute(query)

    songs = []
    for row in c.fetchall():
        songs.append({
            'id': row[0],
            'title': row[1],
            'description': row[2],
            'file_path': row[3]
        })

    conn.close()
    return jsonify(songs)


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

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('INSERT INTO words (tai_khamyang, english, assamese, audio_path) VALUES (?, ?, ?, ?)',
                  (tai_khamyang, english, assamese, audio_path))
        conn.commit()
        word_id = c.lastrowid
        conn.close()

        return jsonify({'success': True, 'id': word_id})

    except Exception as e:
        print(f"Error adding word: {e}")
        return jsonify({'error': str(e)}), 500


#words
@app.route('/api/words/<int:word_id>', methods=['PUT'])
def update_word(word_id):
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = None
    try:
        # Initialize variables
        tai_khamyang = None
        english = None
        assamese = None
        audio_path = None

        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            tai_khamyang = data.get('tai_khamyang')
            english = data.get('english')
            assamese = data.get('assamese')
        else:
            tai_khamyang = request.form.get('tai_khamyang')
            english = request.form.get('english')
            assamese = request.form.get('assamese')

            # Handle file upload if present
            audio_file = request.files.get('audio')
            if audio_file:
                filename = secure_filename(audio_file.filename)
                audio_path = filename
                audio_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Validate required fields
        if not all([tai_khamyang, english, assamese]):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        # Update with or without audio path
        if audio_path:
            c.execute('UPDATE words SET tai_khamyang=?, english=?, assamese=?, audio_path=? WHERE id=?',
                      (tai_khamyang, english, assamese, audio_path, word_id))
        else:
            c.execute('UPDATE words SET tai_khamyang=?, english=?, assamese=? WHERE id=?',
                      (tai_khamyang, english, assamese, word_id))

        conn.commit()
        return jsonify({'message': 'Word updated successfully'})

    except Exception as e:
        print(f'Error in update_word: {e}')
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/words/<int:word_id>', methods=['DELETE'])
def delete_word(word_id):
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('DELETE FROM words WHERE id=?', (word_id,))
        conn.commit()
        conn.close()
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

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('INSERT INTO songs (title, description, file_path) VALUES (?, ?, ?)',
                  (title, description, file_path))
        conn.commit()
        song_id = c.lastrowid
        conn.close()

        return jsonify({'success': True, 'id': song_id})

    except Exception as e:
        print(f"Error adding song: {e}")
        return jsonify({'error': str(e)}), 500


#song
@app.route('/api/songs/<int:song_id>', methods=['PUT'])
def update_song(song_id):
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = None
    try:
        # Initialize variables
        title = None
        description = None
        file_path = None

        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            title = data.get('title')
            description = data.get('description')
        else:
            title = request.form.get('title')
            description = request.form.get('description')

            # Handle file upload if present
            audio_file = request.files.get('audio')
            if audio_file:
                filename = secure_filename(audio_file.filename)
                file_path = filename
                audio_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Validate required fields
        if not title:
            return jsonify({'error': 'Title is required'}), 400

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        # Update with or without file path
        if file_path:
            c.execute('UPDATE songs SET title=?, description=?, file_path=? WHERE id=?',
                      (title, description, file_path, song_id))
        else:
            c.execute('UPDATE songs SET title=?, description=? WHERE id=?',
                      (title, description, song_id))

        conn.commit()
        return jsonify({'message': 'Song updated successfully'})

    except Exception as e:
        print(f'Error in update_song: {e}')
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/songs/<int:song_id>', methods=['DELETE'])
def delete_song(song_id):
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('DELETE FROM songs WHERE id=?', (song_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)