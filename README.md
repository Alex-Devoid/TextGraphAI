# Generalized Entity Extraction with GraphRAG

This project is a Python package designed to build a knowledge graph from entity extraction of various source documents like transcripts, house bills, PDFs, and other similar documents using GraphRAG.

## Features

- User Registration and Login
- Project Management
- Document Upload
- Entity Extraction from Documents
- Knowledge Graph Construction with Neo4j
- Retrieval-Augmented Generation (RAG) with Knowledge Graphs

## Pre-processing and Annotation

### Pre-process Text Data

To clean and segment your text data, run the pre-processing script:

```sh
python preprocess.py --input <input_file_or_directory> --output <output_directory> --chunk_size <chunk_size>
```

### Annotate Text Data with GPT-4

To annotate the pre-processed text data using GPT-4, run the annotation script:

```sh
python annotate.py --input <input_directory> --output <output_directory>
```

## Running the Application

### Option 1: Using Docker (Recommended)

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
OPENAI_API_KEY=your_openai_api_key_here
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

## Using Sample Data

### Download Sample Data

To download the sample transcript, run the following script:

```sh
cd journalistic-entity-extraction/sample_data
python download_transcript.py
```

This will download the full transcript from the specified URL and save it as `full_transcript.txt`.

### Sample House Bill PDF

A sample PDF file named `sample_house_bill.pdf` is also provided in the `sample_data` directory.

### Using the Sample Data

1. **Register a New User**:

Go to the registration section in the web interface and create a new user.

2. **Create a New Project**:

Go to the project creation section and create a new project with a name of your choice.

3. **Upload Documents**:

- **Transcript**: Upload `sample_data/full_transcript.txt`.
- **House Bill PDF**: Upload `sample_data/BILLS-118hr5863rfs.pdf`.

4. **Extract Entities and Build Knowledge Graph**:

Go to the entity extraction section, select your project, and click on the "Extract" button. The application will process the documents, extract entities, and build a knowledge graph.

5. **View Knowledge Graph**:

Access Neo4j at `http://localhost:7474` with the default credentials (`neo4j/test`) to visualize the knowledge graph. You can run queries to explore the relationships between the extracted entities.

## Using RAG with Knowledge Graphs

### RAG Endpoint

You can use the RAG functionality by sending a POST request to the `/rag/` endpoint with your query. The app will retrieve relevant information from the knowledge graph and use it to generate a response.

#### Example Usage

```sh
http POST http://localhost:8000/rag/ user_query="Tell me about the environmental bill."
```

This will return a response generated using the retrieved information from the knowledge graph and the language model.

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
│   │       ├── knowledge_graph.py
│   │       ├── rag.py
│   │       ├── retrieval.py
│   ├── requirements.txt
│   ├── sample_data/
│   │   ├── BILLS-118hr5863rfs.pdf
│   │   ├── download_transcript.py
│   │   ├── full_transcript.txt
│   │   ├── preprocessed/
│   │   ├── annotated/
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
