from flask import Flask, render_template, request, send_from_directory, redirect, url_for, flash
import os
import random
import logging
from logging.handlers import RotatingFileHandler
import time
from werkzeug.utils import secure_filename
import subprocess  # For executing commands
from functions import *
import psycopg2

app = Flask(__name__)
app.secret_key = "FakeSecretKey"  # Important pour les sessions et les flash messages

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Obtention de la localisation à partir de la variable d'environnement
if 'LOCATION_NAME' in os.environ:
    app.config['LOCATION_NAME'] = os.environ['LOCATION_NAME']
else:
    greek_letters = ['Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon']
    app.config['LOCATION_NAME'] = random.choice(greek_letters)

# Configuration du dossier logs
logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Configuration du logging
log_file = os.path.join(logs_dir, 'app.log')
file_handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024 * 10, backupCount=5)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.DEBUG)

def get_file_info(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    size = os.path.getsize(filepath) / (1024)
    name, ext = os.path.splitext(filename)
    return {'name': name, 'ext': ext, 'size': round(size, 2)}

@app.route('/', methods=['GET', 'POST'])
def index():
    user_ip = request.remote_addr
    location_name = app.config['LOCATION_NAME']
    message = None
    success = False

    files = [get_file_info(f) for f in os.listdir(UPLOAD_FOLDER)]

    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                try:
                    file.save(filepath)
                    message = 'Fichier téléchargé avec succès!'
                    success = True
                    app.logger.info(f"File '{file.filename}' uploaded successfully.")
                except Exception as e:
                    message = "Erreur lors de l'upload"
                    success = False
                    app.logger.error(f"Error uploading file '{file.filename}': {e}")
            else:
                message = 'Aucun fichier sélectionné'

        elif 'selected_files' in request.form:
            if 'download' in request.form:
                selected_files = request.form.getlist('selected_files')
                for filename in selected_files:
                    time.sleep(1)  # Ajout d'un délai d'une seconde
                    app.logger.info(f"File '{filename}' downloaded.")
                    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
            elif 'delete' in request.form:
                selected_files = request.form.getlist('selected_files')
                for filename in selected_files:
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    try:
                        os.remove(filepath)
                        message = 'Fichiers sélectionnés supprimés avec succès!'
                        success = True
                        app.logger.info(f"File '{filename}' deleted.")
                    except Exception as e:
                        message = "Erreur lors de la suppression des fichiers"
                        success = False
                        app.logger.error(f"Error deleting file '{filename}': {e}")
                files = [get_file_info(f) for f in os.listdir(UPLOAD_FOLDER)]

    return render_template('index.html', user_ip=user_ip, location_name=location_name, message=message, success=success, files=files)

@app.route('/refresh')
def refresh():
    app.logger.info("Page refreshed.")
    return redirect(url_for('index'))

@app.route('/logs', methods=['GET', 'POST'])
def logs():
    if request.method == 'POST':
        if 'clear_logs' in request.form:
            try:
                open(log_file, 'w').close() # Efface le contenu du fichier de log
                app.logger.info("Logs cleared.")
            except Exception as e:
                app.logger.error(f"Error clearing logs: {e}")
            return redirect(url_for('logs')) # Redirige vers la page de logs pour rafraichir
    try:
        with open(log_file, 'r') as f:
            log_content = f.read()
        return render_template('logs.html', log_content=log_content)
    except FileNotFoundError:
        return "Logs non trouvés", 404

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Ici, vous implémenteriez votre logique d'authentification
        # Dans cet exemple, nous allons simplement simuler une authentification réussie
        if username == 'test' and password == 'test':
            # Authentification réussie
            flash('Login successful!', 'success')
            app.logger.info(f"User '{username}' login successful")
            return redirect(url_for('index'))  # Rediriger vers la page d'accueil
        else:
            # Authentification échouée
            app.logger.error(f"User '{username}' : credentials invalid")
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')

@app.route('/payment')
def payment():
    return render_template('payment.html')

@app.route('/process_payment', methods=['POST'])
def process_payment():
    app.logger.info(f"Fake payment processed")
    return render_template('payment_result.html')

@app.route('/video/<filename>')
def show_video(filename):
    return render_template('video.html', video_filename=filename)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/ads')
def show_ads():
    return render_template('ads.html')

@app.route('/network_tools', methods=['GET', 'POST'])
def network_tools():
    result = None
    tool = request.form.get('tool')

    if request.method == 'POST':
        target = request.form.get('target')
        sql_port = request.form.get('sql_port')
        sql_db_name = request.form.get('sql_db_name')
        sql_user = request.form.get('sql_user')
        sql_password = request.form.get('sql_password')
        sql_query = request.form.get('sql_query')

        # **SECURE Input Validation**
        if not target:
            result = "Error: Target host/IP is required."
            return render_template('network_tools.html', result=result, tool=tool)

        # Validate target
        if not (is_valid_hostname(target) or is_valid_ipv4_address(target) or is_valid_ipv6_address(target)):
            result = "Error: Invalid target host/IP."
            return render_template('network_tools.html', result=result, tool=tool)

        if tool == 'ping':
            try:
                command = ['ping', '-c', '4', target]
                process = subprocess.Popen(command, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
                result = stdout.decode() + stderr.decode()
            except Exception as e:
                result = f"Error: {e}"

        elif tool == 'traceroute':
            try:
                # Check if traceroute is available and use the appropriate command
                if os.name == 'nt':  # Windows
                    command = ['tracert', target]
                else:  # Unix-like systems (Linux, macOS)
                    traceroute_path = '/bin/traceroute'
                    if not os.path.exists(traceroute_path):
                        result = f"Error: traceroute command not found at {traceroute_path} or /usr/sbin/traceroute"
                        return render_template('network_tools.html', result=result, tool=tool)
                    command = [traceroute_path, target]
                process = subprocess.Popen(command, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
                result = stdout.decode() + stderr.decode()
            except Exception as e:
                result = f"Error: {e}"

        elif tool == 'sql' and sql_query:
            try:
                # Securely handle database credentials!
                conn = psycopg2.connect(
                    host=target or os.environ.get('DB_HOST'),  # Use 'target' for SQL host
                    port=sql_port or os.environ.get('DB_PORT'),
                    dbname=sql_db_name or os.environ.get('DB_NAME'),
                    user=sql_user or os.environ.get('DB_USER'),
                    password=sql_password or os.environ.get('DB_PASSWORD')
                )
                cur = conn.cursor()
                cur.execute(sql_query)
                if cur.description:
                    result = cur.fetchall()
                    result = str(result)
                else:
                    result = "Query executed successfully, no results to display."
                conn.commit()
                cur.close()
                conn.close()
            except psycopg2.Error as e:
                result = f"Error executing SQL: {e}"
            except Exception as e:
                result = f"Error: {e}"
        else:
            result = "Error: Invalid tool selected."

    return render_template('network_tools.html', result=result, tool=tool)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)