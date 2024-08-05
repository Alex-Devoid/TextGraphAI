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


## Uploading Documents

To upload a document:

1. Open your web browser and navigate to [http://localhost:5001](http://localhost:5001).
2. Use the upload form to select a file.
3. (Optional) Select `uploads/transcriptLC68920.txt` to test tool with a transcript of a U.S. Senrtate hearing.
4. Click the upload button to submit the file for processing.
5. Extraction prompts will automatically be fine tuned based on the text you uplaoded.
6. GraphRAG indexing status is currently not visible in `docker-compose logs -f celery-worker`, but will notify you when indexing finishes after several miniets. 
- `Settings.yaml`is configured to use OpenAI models `gpt-4o-mini` and `text-embedding-3-small`.
- Completion logs look like this:
```
textgraphai-celery-worker-1  | ⠋ GraphRAG Indexer 
textgraphai-celery-worker-1  | ├── Loading Input (text) - 1 files loaded (0 filtered) ━━━━━━ 100% 0:00:… 0:00:…
textgraphai-celery-worker-1  | ├── create_base_text_units
textgraphai-celery-worker-1  | ├── create_base_extracted_entities
textgraphai-celery-worker-1  | ├── create_summarized_entities
textgraphai-celery-worker-1  | ├── create_base_entity_graph
textgraphai-celery-worker-1  | ├── create_final_entities
textgraphai-celery-worker-1  | ├── create_final_nodes
textgraphai-celery-worker-1  | ├── create_final_communities
textgraphai-celery-worker-1  | ├── join_text_units_to_entity_ids
textgraphai-celery-worker-1  | ├── create_final_relationships
textgraphai-celery-worker-1  | ├── join_text_units_to_relationship_ids
textgraphai-celery-worker-1  | ├── create_final_community_reports
textgraphai-celery-worker-1  | ├── create_final_text_units
textgraphai-celery-worker-1  | ├── create_base_documents
textgraphai-celery-worker-1  | └── create_final_documents🚀 All workflows completed successfully.
```

When the knowledge graph is loaded into Neo4j, you will see a message like this:
```
textgraphai-celery-worker-1  | [2024-08-05 04:42:49,595: INFO/ForkPoolWorker-4] Task app.tasks.trigger_neo4j_import[987ccdd2-c497-450f-9a83-6516eae70a24] succeeded in 40.007517769s: None
```


## Viewing Neo4j Database

### Using Neo4j Desktop Application

1. Open the [Neo4j Desktop application](https://neo4j.com/download/?utm_source=Google&utm_medium=PaidSearch&utm_campaign=Evergreen&utm_content=AMS-Search-SEMBrand-Evergreen-None-SEM-SEM-NonABM&utm_term=download%20neo4j&utm_adgroup=download&gad_source=1&gclid=Cj0KCQjwzby1BhCQARIsAJ_0t5MPiON1FsQVy85OZEZAS332LfsIOniodk-9z0h2vfw1QWrLDmB1YAUaAs6DEALw_wcB).
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

## Global Search Example:
```
docker exec -it textgraphai-celery-worker-1 python -m graphrag.query --root app --method global "What are the top themes in this transcript?"
```

output:
```
UCCESS: Global Search Response: # Key Themes in the Transcript

The analysis of the dataset reveals several prominent themes that are critical to understanding the current landscape of environmental management, energy efficiency, and water resource management. Below are the top themes identified:

## 1. **Funding for Environmental and Energy Initiatives**
The importance of funding for various environmental and energy initiatives is a recurring theme. Discussions surrounding the Fiscal Year 2022 budget highlight the advocacy efforts of organizations such as The Nature Conservancy and the American Geophysical Union, which are crucial for sustaining these initiatives [Data: Reports (245, 267, 206, 158, 228, +more)].

## 2. **Water Management and Conservation**
Water management, particularly concerning the Colorado River and its surrounding communities, is a significant focus. Entities like the Grand Valley Irrigation Company and the Bureau of Reclamation play vital roles in managing water resources and addressing salinity control [Data: Reports (305, 290, 302)]. Additionally, the recovery of endangered species and compliance with federal regulations, such as the Endangered Species Act, are critical aspects of water management efforts in regions like New Mexico [Data: Reports (289, 306, 131)].

## 3. **Energy Efficiency Advocacy**
Energy efficiency is emphasized through the roles of organizations like E4TheFuture, BPA, and BPI, which collaborate to promote clean energy initiatives and enhance energy efficiency programs [Data: Reports (144, 296, 307, 242, 251)]. The Weatherization Assistance Program (WAP) is also highlighted for its role in improving energy efficiency in homes, particularly for low-income households [Data: Reports (252)].

## 4. **Technological Innovation in Energy**
The U.S. is recognized as a leader in energy technology, with initiatives like ARPA-E supporting high-risk, long-term energy projects essential for maintaining competitiveness in the global energy landscape [Data: Reports (261)]. The role of hydrogen energy initiatives and the Clean Energy Technologies Initiative (CFTI) in promoting sustainable energy solutions is also a key theme [Data: Reports (242, 273), (44, +more)].

## 5. **Collaboration Among Stakeholders**
Collaboration among various stakeholders, including federal agencies, state governments, and local communities, is emphasized throughout discussions on water management, energy policies, and conservation efforts. This interconnectedness is crucial for addressing environmental challenges effectively [Data: Reports (66, 284, 288)].

## Conclusion
The themes identified in the dataset underscore the interconnectedness of funding, water management, energy efficiency, technological innovation, and collaboration among stakeholders. These elements are essential for advancing sustainability goals and addressing the pressing environmental challenges faced today. The ongoing advocacy for funding and policy support remains critical for the success of these initiatives.
```
* You may also see errors and warnings realted to setting values in a Pandas DataFrame and parsing JSON responses from the GraphRAG search function. 