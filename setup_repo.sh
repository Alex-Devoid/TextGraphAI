# Create the directory structure
mkdir -p journalistic-entity-extraction/journalistic_entity_extraction/services
mkdir -p journalistic-entity-extraction/templates
mkdir -p journalistic-entity-extraction/static
mkdir -p journalistic-entity-extraction/tests

# Create .gitignore
cat > .gitignore <<EOL
__pycache__/
*.pyc
*.pyo
*.pyd
env/
venv/
*.sqlite3
.DS_Store
EOL

# Create __init__.py
cat > journalistic-entity-extraction/journalistic_entity_extraction/__init__.py <<EOL
# This file can be left empty or used to initialize the module
EOL

# Create main.py
cat > journalistic-entity-extraction/journalistic_entity_extraction/main.py <<EOL
import os
from fastapi import FastAPI, Depends, UploadFile, File
from sqlalchemy.orm import Session
from . import crud, models, schemas
from .database import SessionLocal, engine
from .services.entity_extraction import extract_entities_from_text
from .services.knowledge_graph import build_knowledge_graph
from py2neo import Graph
from dotenv import load_dotenv

load_dotenv()

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_neo4j():
    graph = Graph(
        os.getenv("NEO4J_URI", "bolt://neo4j:7687"),
        auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "test"))
    )
    return graph

@app.post("/register/", response_model=schemas.UserCreate)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.create_user(db=db, user=user)
    return db_user

@app.post("/projects/", response_model=schemas.ProjectCreate)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    return crud.create_project(db=db, project=project)

@app.post("/projects/{project_id}/documents/")
def upload_document(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_location = f"files/{project_id}/{file.filename}"
    os.makedirs(os.path.dirname(file_location), exist_ok=True)
    with open(file_location, "wb") as f:
        f.write(file.file.read())
    db_document = crud.create_document(db=db, document=schemas.DocumentCreate(
        filename=file.filename, path=file_location, project_id=project_id))
    return db_document

@app.post("/projects/{project_id}/extract_entities/")
def extract_entities(project_id: int, db: Session = Depends(get_db), graph: Graph = Depends(get_neo4j)):
    documents = db.query(models.Document).filter(models.Document.project_id == project_id).all()
    entities = []
    for doc in documents:
        with open(doc.path, "r") as f:
            text = f.read()
            entities.extend(extract_entities_from_text(text))
    knowledge_graph = build_knowledge_graph(graph, entities)
    return {"entities": entities, "knowledge_graph": knowledge_graph}
EOL

# Create models.py
cat > journalistic-entity-extraction/journalistic_entity_extraction/models.py <<EOL
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    path = Column(String)
    project_id = Column(Integer, ForeignKey("projects.id"))
EOL

# Create schemas.py
cat > journalistic-entity-extraction/journalistic_entity_extraction/schemas.py <<EOL
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str

class ProjectCreate(BaseModel):
    name: str

class DocumentCreate(BaseModel):
    filename: str
    path: str
    project_id: int
EOL

# Create crud.py
cat > journalistic-entity-extraction/journalistic_entity_extraction/crud.py <<EOL
from sqlalchemy.orm import Session
from . import models, schemas

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(username=user.username, hashed_password=user.password)  # Hash password in real app
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_project(db: Session, project: schemas.ProjectCreate):
    db_project = models.Project(name=project.name)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def get_projects(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Project).offset(skip).limit(limit).all()

def create_document(db: Session, document: schemas.DocumentCreate):
    db_document = models.Document(**document.dict())
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document
EOL

# Create database.py
cat > journalistic-entity-extraction/journalistic_entity_extraction/database.py <<EOL
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@journalistic_db:5432/journalistic")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
EOL

# Create __init__.py in services
cat > journalistic-entity-extraction/journalistic_entity_extraction/services/__init__.py <<EOL
# This file can be left empty or used to initialize the module
EOL

# Create entity_extraction.py
cat > journalistic-entity-extraction/journalistic_entity_extraction/services/entity_extraction.py <<EOL
# Placeholder for entity extraction logic

def extract_entities_from_text(text: str):
    # Simulate entity extraction
    return [{"text": "Entity", "type": "ORG", "start": 10, "end": 20}]
EOL

# Create knowledge_graph.py
cat > journalistic-entity-extraction/journalistic_entity_extraction/services/knowledge_graph.py <<EOL
from py2neo import Graph, Node, Relationship

def build_knowledge_graph(graph: Graph, entities):
    for entity in entities:
        node = Node(entity['type'], name=entity['text'])
        graph.merge(node, entity['type'], 'name')
    return "Knowledge graph updated"
EOL

# Create index.html
cat > journalistic-entity-extraction/templates/index.html <<EOL
<!DOCTYPE html>
<html>
<head>
    <title>journalistic Tool</title>
</head>
<body>
    <h1>journalistic Tool</h1>
    <div>
        <h2>Register</h2>
        <form id="register-form">
            <label>Username:</label>
            <input type="text" id="username">
            <label>Password:</label>
            <input type="password" id="password">
            <button type="submit">Register</button>
        </form>
    </div>
    <div>
        <h2>Create Project</h2>
        <form id="project-form">
            <label>Project Name:</label>
            <input type="text" id="project-name">
            <button type="submit">Create</button>
        </form>
    </div>
    <div>
        <h2>Upload Document</h2>
        <form id="upload-form">
            <label>Project ID:</label>
            <input type="text" id="project-id">
            <label>Document:</label>
            <input type="file" id="document">
            <button type="submit">Upload</button>
        </form>
    </div>
    <div>
        <h2>Extract Entities</h2>
        <form id="extract-form">
            <label>Project ID:</label>
            <input type="text" id="extract-project-id">
            <button type="submit">Extract</button>
        </form>
        <pre id="entities-output"></pre>
    </div>
    <script src="../static/main.js"></script>
</body>
</html>
EOL

# Create main.js
cat > journalistic-entity-extraction/static/main.js <<EOL
document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const response = await fetch('/register/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
    });
    const result = await response.json();
    alert(\`Registered: \${result.username}\`);
});

document.getElementById('project-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('project-name').value;
    const response = await fetch('/projects/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name }),
    });
    const result = await response.json();
    alert(\`Project Created: \${result.name}\`);
});

document.getElementById('upload-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const projectId = document.getElementById('project-id').value;
    const fileInput = document.getElementById('document');
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    const response = await fetch(\`/projects/\${projectId}/documents/\`, {
        method: 'POST',
        body: formData,
    });
    const result = await response.json();
    alert(\`Document Uploaded: \${result.filename}\`);
});

document.getElementById('extract-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const projectId = document.getElementById('extract-project-id').value;
    const response = await fetch(\`/projects/\${projectId}/extract_entities/\`, {
        method: 'POST',
    });
    const result = await response.json();
    document.getElementById('entities-output').textContent = JSON.stringify(result, null, 2);
});
EOL

# Create README.md
cat > journalistic-entity-extraction/README.md <<EOL
# journalistic Entity Extraction

This project is a Python package designed to build a knowledge graph from entity extraction of various source documents like transcripts, house bills, PDFs, and other similar documents.

## Features

- User Registration and Login
- Project Management
- Document Upload
- Entity Extraction from Documents
- Knowledge Graph Construction with Neo4j

## Installation

To install the package, you can use \`pip\`:

\`\`\`sh
pip install git+https://github.com/yourusername/TEXTGRAPHAI.git
\`\`\`

## Running the Application

### Option 1: Using Docker

1. **Navigate to the \`journalistic-entity-extraction\` directory**:

\`\`\`sh
cd journalistic-entity-extraction
\`\`\`

2. **Start the Services**:

\`\`\`sh
docker-compose up --build
\`\`\`

3. **Access the Application**:

Open your web browser and go to \`http://localhost:8000\` to access the FastAPI application. Neo4j will be accessible at \`http://localhost:7474\` with the default credentials \`neo4j/test\`.

### Option 2: Local Setup

1. **Navigate to the \`journalistic-entity-extraction\` directory**:

\`\`\`sh
cd journalistic-entity-extraction
\`\`\`

2. **Install Dependencies**:

\`\`\`sh
pip install -r requirements.txt
\`\`\`

3. **Set Up Environment Variables**:

Create a \`.env\` file in the \`journalistic-entity-extraction\` directory with the following content:

\`\`\`plaintext
DATABASE_URL=postgresql://user:password@localhost:5432/journalistic
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=test
\`\`\`

4. **Run PostgreSQL and Neo4j Locally**:

Ensure you have PostgreSQL and Neo4j running locally. You can download and install them from their official websites.

5. **Initialize the Database**:

Run the following commands to initialize the PostgreSQL database:

\`\`\`sh
psql -U user -d journalistic -c "CREATE TABLE users (id SERIAL PRIMARY KEY, username VARCHAR(50) UNIQUE NOT NULL, hashed_password VARCHAR(100) NOT NULL);"
psql -U user -d journalistic -c "CREATE TABLE projects (id SERIAL PRIMARY KEY, name VARCHAR(100) NOT NULL, owner_id INTEGER REFERENCES users(id));"
psql -U user -d journalistic -c "CREATE TABLE documents (id SERIAL PRIMARY KEY, filename VARCHAR(100) NOT NULL, path VARCHAR(200) NOT NULL, project_id INTEGER REFERENCES projects(id));"
\`\`\`

6. **Start the FastAPI Application**:

\`\`\`sh
uvicorn journalistic_entity_extraction.main:app --reload
\`\`\`

7. **Access the Application**:

Open your web browser and go to \`http://localhost:8000\` to access the FastAPI application.

## Usage

### Example with Hypothetical Transcript and House Bill PDF

Follow these steps to create a knowledge graph using automated entity extraction from a hypothetical transcript and a PDF of a house bill.

1. **Register a New User**:

Go to the registration section in the web interface and create a new user.

2. **Create a New Project**:

Go to the project creation section and create a new project with a name of your choice.

3. **Upload Documents**:

- **Transcript**: Upload a text file containing the transcript.
- **House Bill PDF**: Upload a PDF file of the house bill.

4. **Extract Entities and Build Knowledge Graph**:

Go to the entity extraction section, select your project, and click on the "Extract" button. The application will process the documents, extract entities, and build a knowledge graph.

5. **View Knowledge Graph**:

Access Neo4j at \`http://localhost:7474\` with the default credentials (\`neo4j/test\`) to visualize the knowledge graph. You can run queries to explore the relationships between the extracted entities.

### Sample Data

You can use the following sample data for testing:

**Hypothetical Transcript (transcript.txt)**:
\`\`\`
Today, we are gathered here to discuss the new house bill introduced by Senator John Doe. The bill focuses on environmental conservation and renewable energy resources.
\`\`\`

**House Bill PDF (house_bill.pdf)**:
\`\`\`
HOUSE BILL NO. 1234

An Act to promote renewable energy and environmental conservation.

Introduced by: Senator John Doe
\`\`\`

### Sample Workflow

1. **Register a User**:
    - Username: \`testuser\`
    - Password: \`testpass\`

2. **Create a Project**:
    - Project Name: \`Environmental Bill Analysis\`

3. **Upload Documents**:
    - Upload \`transcript.txt\`
    - Upload \`house_bill.pdf\`

4. **Extract Entities and Build Knowledge Graph**:
    - Select the project \`Environmental Bill Analysis\`
    - Click "Extract"

5. **View Knowledge Graph**:
    - Open Neo4j at \`http://localhost:7474\`
    - Username: \`neo4j\`
    - Password: \`test\`
    - Run queries to explore the graph.

## Project Structure

\`\`\`
TEXTGRAPHAI/
├── journalistic-entity-extraction/
│   ├── Dockerfile
│   ├── README.md
│   ├── docker-compose.yml
│   ├── journalistic_entity_extraction/
│   │   ├── __init__.py
│   │   ├── crud.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── entity_extraction.py
│   │       └── knowledge_graph.py
│   ├── requirements.txt
│   ├── setup.py
│   ├── static/
│   │   └── main.js
│   ├── templates/
│   │   └── index.html
│   └── tests/
│       ├── __init__.py
│       └── test_main.py
├── .gitignore
└── setup_repo.sh
\`\`\`

## Future Enhancements

This MVP is designed to be scalable. Future enhancements can include:

- Advanced entity extraction using machine learning models
- Visualization tools for the knowledge graph
- Integration with external data sources
- User roles and permissions management

## License

This project is licensed under the MIT License.
EOL

# Create setup.py
cat > journalistic-entity-extraction/setup.py <<EOL
from setuptools import setup, find_packages

setup(
    name="journalistic_entity_extraction",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "pydantic",
        "py2neo",
        "python-dotenv"
    ],
    entry_points={
        'console_scripts': [
            'journalistic_entity_extraction=journalistic_entity_extraction.main:app',
        ],
    },
)
EOL

# Create requirements.txt
cat > journalistic-entity-extraction/requirements.txt <<EOL
fastapi
uvicorn
sqlalchemy
pydantic
py2neo
python-dotenv
EOL

# Create __init__.py in tests
cat > journalistic-entity-extraction/tests/__init__.py <<EOL
# This file can be left empty or used to initialize the module
EOL

# Create test_main.py
cat > journalistic-entity-extraction/tests/test_main.py <<EOL
from fastapi.testclient import TestClient
from journalistic_entity_extraction.main import app

client = TestClient(app)

def test_register():
    response = client.post("/register/", json={"username": "testuser", "password": "testpass"})
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

def test_create_project():
    response = client.post("/projects/", json={"name": "Test Project"})
    assert response.status_code == 200
    assert response.json()["name"] == "Test Project"
EOL

# Create docker-compose.yml
cat > journalistic-entity-extraction/docker-compose.yml <<EOL
version: '3.8'

services:
  app:
    build: .
    container_name: journalistic_app
    ports:
      - "8000:80"
    depends_on:
      - db
      - neo4j

  db:
    image: postgres:latest
    container_name: journalistic_db
    environment:
      POSTGRES_DB: journalistic
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  neo4j:
    image: neo4j:latest
    container_name: neo4j
    environment:
      NEO4J_AUTH: "neo4j/test"
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data

volumes:
  postgres_data:
  neo4j_data:
EOL

# Create Dockerfile
cat > journalistic-entity-extraction/Dockerfile <<EOL
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Run the application
CMD ["uvicorn", "journalistic_entity_extraction.main:app", "--host", "0.0.0.0", "--port", "80"]
EOL

echo "All files have been created successfully!"
