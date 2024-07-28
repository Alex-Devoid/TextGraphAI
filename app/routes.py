from flask import Blueprint, render_template, request, redirect, url_for
from app.tasks import process_file
import os

main = Blueprint('main', __name__)

@main.route('/')
def upload_form():
    return render_template('upload.html')

@main.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)
        process_file.delay(file_path)
        return redirect(url_for('main.upload_form'))

@main.route('/results/<filename>')
def results(filename):
    # Placeholder for displaying results
    return f'Results for {filename}'
