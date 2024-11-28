# Flask application entry point
from flask import Flask, render_template, redirect, request, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DATABASE = 'database.db'


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']

        conn = get_db()
        cursor = conn.cursor()

        # Check if username already exists
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            flash('Username already exists!')
            return redirect(url_for('signup'))

        # Insert user into the database
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                       (username, password, role))
        conn.commit()
        conn.close()

        flash('Signup successful! Please log in.')
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    role = session.get('role')
    if role == 'admin':
        return render_template('admin.html', username=session['username'])
    elif role == 'manager':
        return render_template('manager.html', username=session['username'])
    else:
        return render_template('member.html', username=session['username'])


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))


# Route pour le PLM Dashboard
@app.route('/plm_dashboard')
def plm_dashboard():
    # Vérifiez si l'utilisateur est connecté avant d'afficher la page
    if 'username' in session:
        return render_template('plm_dashboard.html')
    else:
        return redirect(url_for('login'))  # Rediriger vers la page de connexion si non connecté


# Route pour la création de projet
@app.route('/create_project', methods=['GET', 'POST'])
def create_project():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        project_name = request.form['project_name']
        project_description = request.form['project_description']
        bom_name = request.form['bom_name']
        bom_fields = request.form['bom_fields']
        
        # Ajouter le projet dans la base de données
        conn = get_db_connection()
        with conn:
            conn.execute('''
                INSERT INTO projects (name, description, bom_name, bom_fields)
                VALUES (?, ?, ?, ?)
            ''', (project_name, project_description, bom_name, bom_fields))
        conn.close()
        return redirect(url_for('view_projects'))
    
    return render_template('create_project.html')


# Route pour visualiser les projets
@app.route('/view_projects')
def view_projects():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    projects = conn.execute('SELECT * FROM projects').fetchall()
    conn.close()
    
    return render_template('view_projects.html', projects=projects)


def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
