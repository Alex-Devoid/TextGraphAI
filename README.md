# journalistic Entity Extraction

This project is a Python package designed to build a knowledge graph from entity extraction of various source documents like transcripts, house bills, PDFs, and other similar documents.

## Features

- User Registration and Login
- Project Management
- Document Upload
- Entity Extraction from Documents
- Knowledge Graph Construction with Neo4j

## Installation

To install the package, you can use `pip`:

```sh
pip install git+https://github.com/Alex-Devoid/TEXTGRAPHAI.git
```

## Running the Application

### Option 1: Using Docker

1. **Navigate to the `journalistic-entity-extraction` directory**:

```sh
cd journalistic-entity-extraction
```

2. **Start the Services**:

```sh
docker-compose up --build
```

3. **Access the Application**:

Open your web browser and go to `http://localhost:8000` to access the FastAPI application. Neo4j will be accessible at `http://localhost:7474` with the default credentials `neo4j/test`.

### Option 2: Local Setup

1. **Navigate to the `journalistic-entity-extraction` directory**:

```sh
cd journalistic-entity-extraction
```

2. **Install Dependencies**:

```sh
pip install -r requirements.txt
```

3. **Set Up Environment Variables**:

Create a `.env` file in the `journalistic-entity-extraction` directory with the following content:

```plaintext
DATABASE_URL=postgresql://user:password@localhost:5432/journalistic
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=test
```

4. **Run PostgreSQL and Neo4j Locally**:

Ensure you have PostgreSQL and Neo4j running locally. You can download and install them from their official websites.

5. **Initialize the Database**:

Run the following commands to initialize the PostgreSQL database:

```sh
psql -U user -d journalistic -c "CREATE TABLE users (id SERIAL PRIMARY KEY, username VARCHAR(50) UNIQUE NOT NULL, hashed_password VARCHAR(100) NOT NULL);"
psql -U user -d journalistic -c "CREATE TABLE projects (id SERIAL PRIMARY KEY, name VARCHAR(100) NOT NULL, owner_id INTEGER REFERENCES users(id));"
psql -U user -d journalistic -c "CREATE TABLE documents (id SERIAL PRIMARY KEY, filename VARCHAR(100) NOT NULL, path VARCHAR(200) NOT NULL, project_id INTEGER REFERENCES projects(id));"
```

6. **Start the FastAPI Application**:

```sh
uvicorn journalistic_entity_extraction.main:app --reload
```

7. **Access the Application**:

Open your web browser and go to `http://localhost:8000` to access the FastAPI application.

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

Access Neo4j at `http://localhost:7474` with the default credentials (`neo4j/test`) to visualize the knowledge graph. You can run queries to explore the relationships between the extracted entities.

### Sample Data

You can use the following sample data for testing:

**Hypothetical Transcript (transcript.txt)**:
```
Today, we are gathered here to discuss the new house bill introduced by Senator John Doe. The bill focuses on environmental conservation and renewable energy resources.
```

**House Bill PDF (house_bill.pdf)**:
```
HOUSE BILL NO. 1234

An Act to promote renewable energy and environmental conservation.

Introduced by: Senator John Doe
```

### Sample Workflow

1. **Register a User**:
    - Username: `testuser`
    - Password: `testpass`

2. **Create a Project**:
    - Project Name: `Environmental Bill Analysis`

3. **Upload Documents**:
    - Upload `transcript.txt`
    - Upload `house_bill.pdf`

4. **Extract Entities and Build Knowledge Graph**:
    - Select the project `Environmental Bill Analysis`
    - Click "Extract"

5. **View Knowledge Graph**:
    - Open Neo4j at `http://localhost:7474`
    - Username: `neo4j`
    - Password: `test`
    - Run queries to explore the graph.

## Project Structure

```
TEXTGRAPHAI/
├── .gitignore
├── README.md
├── journalistic-entity-extraction/
│   ├── Dockerfile
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
└── setup_repo.sh
```

## Future Enhancements

This MVP is designed to be scalable. Future enhancements can include:

- Advanced entity extraction using machine learning models
- Visualization tools for the knowledge graph
- Integration with external data sources
- User roles and permissions management

## License

This project is licensed under the MIT License.
