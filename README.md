# TextGraphAI, a GraphRAG App

This project is a Flask application integrated with Celery for task management, GraphRAG for knowledge graph generation, and Neo4j for graph database storage. The application allows you to upload documents, process them to extract knowledge graphs, and store these graphs in Neo4j.

### Setup

Ensure you have Docker and Docker Compose installed.

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Alex-Devoid/TextGraphAI.git
   cd TextGraphAI
   ```

2. **Create a `.env` file in the `app` directory** (GraphRAG will look for it there) and add the required environment variables:

   ```env
   CELERY_BROKER_URL=redis://redis:6379/0
   CELERY_RESULT_BACKEND=redis://redis:6379/0
   GRAPHRAG_API_KEY=your-graphrag-api-key
   NEO4J_PASSWORD=your-neo4j-password
   ```

   - `CELERY_BROKER_URL`: URL for the Celery message broker (Redis).
   - `CELERY_RESULT_BACKEND`: URL for the Celery result backend (Redis).
   - `GRAPHRAG_API_KEY`: LLM API key for GraphRAG, for example your OpenAI Key.
   - `NEO4J_PASSWORD`: Password for the Neo4j database.

3. **Build and start the Docker containers:**

   ```bash
   docker-compose --env-file app/.env up --build
   ```

   - Ensure your system has enough disk space to avoid issues with Neo4j.

4. The Flask app will be available at [http://localhost:5001](http://localhost:5001).

## Uploading Documents

To upload a document:

1. Open your web browser and navigate to [http://localhost:5001](http://localhost:5001).
2. Use the upload form to select a file, specify a dataset name, and choose whether to create a new dataset or add to an existing one.
3. (Optional) Select `uploads/transcriptLC68920.txt` to test tool with a transcript of a U.S. Senrtate hearing.
4. Click the upload button to submit the file for processing.
5. Keep an eye on 
 

## Viewing Neo4j Database

### Using Neo4j Browser

1. Open the Neo4j Desktop application.
2. Connect to the Neo4j instance running at `bolt://localhost:7687`.
3. Use the credentials specified in your `.env` file (default username: `neo4j`, password: the value of `NEO4J_PASSWORD`).

### Using Neo4j Browser Interface

1. Open your web browser and navigate to [http://localhost:7474](http://localhost:7474).
2. Log in using the Neo4j credentials specified in your `.env` file.
3. You can now query and explore the knowledge graph data.

### Example Cypher Queries

To see 25 nodes in the graph:

```cypher
MATCH (n) RETURN n LIMIT 25
```

To see 25 nodes and their relationships:

```cypher
MATCH (n)
WITH n LIMIT 25
MATCH (n)-[r]->(m)
RETURN n, r, m
```
