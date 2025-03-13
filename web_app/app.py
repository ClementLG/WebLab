from flask import Flask, render_template, request, send_from_directory, redirect, url_for
import os
import random
import logging
from logging.handlers import RotatingFileHandler
import time  # Importation du module time

app = Flask(__name__)

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

if __name__ == '__main__':
    app.run(debug=True)