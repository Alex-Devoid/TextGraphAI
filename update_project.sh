#!/bin/bash

# Create preprocess.py
cat > preprocess.py <<EOL
import os
import re
import argparse

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\[.*?\]', '', text)
    text = text.strip()
    return text

def chunk_text(text, chunk_size=600):
    words = text.split()
    for i in range(0, len(words), chunk_size):
        yield ' '.join(words[i:i+chunk_size])

def preprocess_file(input_file, output_dir, chunk_size=600):
    with open(input_file, 'r') as file:
        text = file.read()
    
    cleaned_text = clean_text(text)
    chunks = list(chunk_text(cleaned_text, chunk_size))

    for i, chunk in enumerate(chunks):
        with open(f"{output_dir}/{os.path.basename(input_file)}_chunk_{i}.txt", 'w') as chunk_file:
            chunk_file.write(chunk)

def preprocess_directory(input_dir, output_dir, chunk_size=600):
    for filename in os.listdir(input_dir):
        if filename.endswith(".txt"):
            preprocess_file(os.path.join(input_dir, filename), output_dir, chunk_size)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Preprocess text data.')
    parser.add_argument('--input', required=True, help='Input file or directory')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--chunk_size', type=int, default=600, help='Chunk size for text segmentation')
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    if os.path.isfile(args.input):
        preprocess_file(args.input, args.output, args.chunk_size)
    elif os.path.isdir(args.input):
        preprocess_directory(args.input, args.output, args.chunk_size)
    else:
        raise ValueError("Invalid input path. Must be a file or directory.")
EOL

# Create annotate.py
cat > annotate.py <<EOL
import openai
import os
import argparse
from dotenv import load_dotenv

load_dotenv()

def annotate_text(text):
    openai.api_key = os.getenv("OPENAI_API_KEY")

    response = openai.Completion.create(
        engine="davinci",
        prompt=f"Annotate the following text with entities and relationships:\n\n{text}",
        max_tokens=1000
    )

    return response.choices[0].text

def annotate_files(input_dir, output_dir):
    for filename in os.listdir(input_dir):
        if filename.endswith(".txt"):
            with open(os.path.join(input_dir, filename), 'r') as file:
                text = file.read()
            
            annotated_text = annotate_text(text)
            
            with open(os.path.join(output_dir, f"annotated_{filename}"), 'w') as output_file:
                output_file.write(annotated_text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Annotate text data with GPT-4.')
    parser.add_argument('--input', required=True, help='Input directory')
    parser.add_argument('--output', required=True, help='Output directory')
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    annotate_files(args.input, args.output)
EOL

# Create graphrag_integration.py
cat > graphrag_integration.py <<EOL
import asyncio
import os
from graphrag.index import run_pipeline
from graphrag.index.config import PipelineCSVInputConfig, PipelineWorkflowReference
from graphrag.index.input import load_input
from dotenv import load_dotenv

load_dotenv()

async def run_graphrag(input_dir):
    if (
        "EXAMPLE_OPENAI_API_KEY" not in os.environ
        and "OPENAI_API_KEY" not in os.environ
    ):
        msg = "Please set EXAMPLE_OPENAI_API_KEY or OPENAI_API_KEY environment variable to run this example"
        raise Exception(msg)

    dataset = await load_input(
        PipelineCSVInputConfig(
            file_pattern=".*\\.txt$",
            base_dir=input_dir,
            source_column="source",
            text_column="text",
            timestamp_column="timestamp",
            timestamp_format="%Y%m%d%H%M%S",
            title_column="title",
        ),
    )

    workflows = [
        PipelineWorkflowReference(
            name="entity_extraction",
            config={
                "entity_extract": {
                    "strategy": {
                        "type": "graph_intelligence",
                        "llm": {
                            "type": "openai_chat",
                            "api_key": os.environ.get(
                                "EXAMPLE_OPENAI_API_KEY",
                                os.environ.get("OPENAI_API_KEY", None),
                            ),
                            "model": os.environ.get(
                                "EXAMPLE_OPENAI_MODEL", "gpt-3.5-turbo"
                            ),
                            "max_tokens": os.environ.get(
                                "EXAMPLE_OPENAI_MAX_TOKENS", 2500
                            ),
                            "temperature": os.environ.get(
                                "EXAMPLE_OPENAI_TEMPERATURE", 0
                            ),
                        },
                    }
                }
            },
        )
    ]

    tables = []
    async for table in run_pipeline(dataset=dataset, workflows=workflows):
        tables.append(table)
    pipeline_result = tables[-1]

    if pipeline_result.result is not None:
        print(pipeline_result.result["entities"].to_list())
    else:
        print("No results!")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Run GraphRAG integration.')
    parser.add_argument('--input', required=True, help='Input directory')
    args = parser.parse_args()

    asyncio.run(run_graphrag(args.input))
EOL

# Update main.py to add the new RAG endpoint and upload file functionality
cat > journalistic-entity-extraction/journalistic_entity_extraction/main.py <<EOL
from fastapi import FastAPI, Depends, UploadFile, File
from sqlalchemy.orm import Session
from . import crud, models, schemas
from .database import SessionLocal, engine
from .services.rag import generate_response
from py2neo import Graph
from dotenv import load_dotenv
import os

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

@app.post("/rag/")
async def rag_endpoint(user_query: str, graph: Graph = Depends(get_neo4j)):
    response = generate_response(graph, user_query)
    return {"response": response}

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_location = f"files/{file.filename}"
    with open(file_location, "wb") as f:
        f.write(file.file.read())
    return {"info": f"file '{file.filename}' saved at '{file_location}'"}
EOL

# Update README.md
cat > README.md <<EOL
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

\`\`\`sh
python preprocess.py --input <input_file_or_directory> --output <output_directory> --chunk_size <chunk_size>
\`\`\`

### Annotate Text Data with GPT-4

To annotate the pre-processed text data using GPT-4, run the annotation script:

\`\`\`sh
python annotate.py --input <input_directory> --output <output_directory>
\`\`\`

## Running the Application

### Option 1: Using Docker (Recommended)

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
OPENAI_API_KEY=your_openai_api_key_here
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

## Using Sample Data

### Download Sample Data

To download the sample transcript, run the following script:

\`\`\`sh
cd journalistic-entity-extraction/sample_data
python download_transcript.py
\`\`\`

This will download the full transcript from the specified URL and save it as \`full_transcript.txt\`.

### Sample House Bill PDF

A sample PDF file named \`sample_house_bill.pdf\` is also provided in the \`sample_data\` directory.

### Using the Sample Data

1. **Register a New User**:

Go to the registration section in the web interface and create a new user.

2. **Create a New Project**:

Go to the project creation section and create a new project with a name of your choice.

3. **Upload Documents**:

- **Transcript**: Upload \`sample_data/full_transcript.txt\`.
- **House Bill PDF**: Upload \`sample_data/BILLS-118hr5863rfs.pdf\`.

4. **Extract Entities and Build Knowledge Graph**:

Go to the entity extraction section, select your project, and click on the "Extract" button. The application will process the documents, extract entities, and build a knowledge graph.

5. **View Knowledge Graph**:

Access Neo4j at \`http://localhost:7474\` with the default credentials (\`neo4j/test\`) to visualize the knowledge graph. You can run queries to explore the relationships between the extracted entities.

## Using RAG with Knowledge Graphs

### RAG Endpoint

You can use the RAG functionality by sending a POST request to the \`/rag/\` endpoint with your query. The app will retrieve relevant information from the knowledge graph and use it to generate a response.

#### Example Usage

\`\`\`sh
http POST http://localhost:8000/rag/ user_query="Tell me about the environmental bill."
\`\`\`

This will return a response generated using the retrieved information from the knowledge graph and the language model.

## Project Structure

\`\`\`
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

echo "Project updated successfully!"
