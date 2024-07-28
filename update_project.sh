#!/bin/bash

# Define the root directory for the project
ROOT_DIR="."

# Create the project directory and subdirectories
mkdir -p $ROOT_DIR/app/templates
mkdir -p $ROOT_DIR/app/static
mkdir -p $ROOT_DIR/app/prompts
mkdir -p $ROOT_DIR/app/logs
mkdir -p $ROOT_DIR/uploads
mkdir -p $ROOT_DIR/output

# Create main files and directories

# run.py
cat <<EOL > $ROOT_DIR/run.py
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
EOL

# celeryconfig.py
cat <<EOL > $ROOT_DIR/celeryconfig.py
broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost:6379/0'
EOL

# requirements.txt
cat <<EOL > $ROOT_DIR/requirements.txt
Flask
Celery
pandas
graphrag
redis
EOL

# README.md
cat <<EOL > $ROOT_DIR/README.md
# GraphRAG App

This is a web application that allows users to upload documents and process them using GraphRAG.

## Installation

1. Clone the repository.
2. Install dependencies using \`pip install -r requirements.txt\`.
3. Run the application with \`python run.py\`.

## Usage

- Navigate to the web interface and upload your documents.
- The backend will process and index the documents using GraphRAG.
- Results can be viewed on the results page.

## Configuration

- Update \`app/settings.yaml\` with your specific settings.

## License

MIT
EOL

# app/__init__.py
cat <<EOL > $ROOT_DIR/app/__init__.py
from flask import Flask
from app.routes import main as main_blueprint
from celery import Celery

def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
    app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
    app.register_blueprint(main_blueprint)
    return app

def create_celery_app(app=None):
    app = app or create_app()
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    celery.autodiscover_tasks(['app.tasks'])
    return celery
EOL

# app/routes.py
cat <<EOL > $ROOT_DIR/app/routes.py
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
EOL

# app/tasks.py
cat <<EOL > $ROOT_DIR/app/tasks.py
from celery import Celery
from graphrag.index import PipelineConfig, run_pipeline_with_config
from graphrag.index.progress import RichProgressReporter
import pandas as pd
import os
import time
import logging
import asyncio
import signal

celery = Celery('tasks', broker='pyamqp://guest@localhost//')

def _enable_logging(root_dir, run_id, verbose):
    logging_file = os.path.join(root_dir, 'logs', f'{run_id}-indexing-engine.log')
    os.makedirs(os.path.dirname(logging_file), exist_ok=True)
    logging.basicConfig(
        filename=logging_file,
        filemode='a',
        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
        datefmt='%H:%M:%S',
        level=logging.DEBUG if verbose else logging.INFO,
    )

def _create_default_config(root, config_path, verbose, dryrun, progress_reporter):
    # Example function to create or load a configuration
    if config_path and os.path.exists(config_path):
        # Load configuration from file
        with open(config_path, 'r') as f:
            config_data = f.read()
        # Assume create_graphrag_config is a function to parse the config
        return create_graphrag_config(config_data, root)
    else:
        # Return default configuration
        return PipelineConfig()

@celery.task
def process_file(file_path):
    root = 'app'  # Define your root path
    run_id = time.strftime("%Y%m%d-%H%M%S")
    _enable_logging(root, run_id, verbose=True)
    progress_reporter = RichProgressReporter("GraphRAG Indexer")

    # Create or load the pipeline configuration
    pipeline_config = _create_default_config(
        root, config_path=os.path.join(root, 'settings.yaml'), verbose=True, dryrun=False, progress_reporter=progress_reporter
    )
    cache = None  # Define caching strategy if needed

    async def execute():
        encountered_errors = False
        async for output in run_pipeline_with_config(
            pipeline_config,
            run_id=run_id,
            memory_profile=False,
            cache=cache,
            progress_reporter=progress_reporter,
        ):
            if output.errors:
                encountered_errors = True
                progress_reporter.error(output.workflow)
            else:
                progress_reporter.success(output.workflow)
            progress_reporter.info(str(output.result))

        if encountered_errors:
            progress_reporter.error("Errors occurred during the pipeline run, see logs for more details.")
        else:
            progress_reporter.success("All workflows completed successfully.")

    def handle_signal(signum, frame):
        logging.info(f"Received signal {signum}, exiting...")
        for task in asyncio.all_tasks():
            task.cancel()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    asyncio.run(execute())
EOL

# app/utils.py
cat <<EOL > $ROOT_DIR/app/utils.py
# Utility functions can be added here
EOL

# app/templates/upload.html
cat <<EOL > $ROOT_DIR/app/templates/upload.html
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Upload File</title>
</head>
<body>
    <h1>Upload File</h1>
    <form method="post" enctype="multipart/form-data" action="/upload">
        <input type="file" name="file">
        <input type="submit" value="Upload">
    </form>
</body>
</html>
EOL

# app/settings.yaml
cat <<EOL > $ROOT_DIR/app/settings.yaml
# settings.yaml example
api_key: "YOUR_API_KEY"
# Add other necessary settings
EOL

# app/prompts/claim_extraction.txt
cat <<EOL > $ROOT_DIR/app/prompts/claim_extraction.txt
# Content for claim extraction prompt
EOL

# app/prompts/community_report.txt
cat <<EOL > $ROOT_DIR/app/prompts/community_report.txt
# Content for community report prompt
EOL

# app/prompts/entity_extraction.txt
cat <<EOL > $ROOT_DIR/app/prompts/entity_extraction.txt
# Content for entity extraction prompt
EOL

# app/prompts/summarize_descriptions.txt
cat <<EOL > $ROOT_DIR/app/prompts/summarize_descriptions.txt
# Content for summarize descriptions prompt
EOL

# Dockerfile for Flask app
cat <<EOL > $ROOT_DIR/Dockerfile
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=run.py

# Run the command to start the Flask server
CMD ["flask", "run", "--host=0.0.0.0"]
EOL

# Dockerfile for Celery worker
cat <<EOL > $ROOT_DIR/Dockerfile.celery
# Use the same base image as the Flask app for consistency
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Define the Celery worker entry point
CMD ["celery", "-A", "app.tasks", "worker", "--loglevel=info"]
EOL

# docker-compose.yml
cat <<EOL > $ROOT_DIR/docker-compose.yml
version: '3'
services:
  flask-app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    volumes:
      - .:/usr/src/app
    depends_on:
      - redis

  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile.celery
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    volumes:
      - .:/usr/src/app
    depends_on:
      - redis

  redis:
    image: redis:latest
    ports:
      - "6379:6379"
EOL

echo "Project structure and files created successfully!"
