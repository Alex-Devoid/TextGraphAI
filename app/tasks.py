import logging
import os
import subprocess
from pydantic import BaseModel
from celery import Celery
from graphrag.index import PipelineConfig, create_pipeline_config, run_pipeline_with_config
from graphrag.index.progress.rich import RichProgressReporter
from graphrag.index.progress import NullProgressReporter, PrintProgressReporter, ProgressReporter
from graphrag.index.cache import NoopPipelineCache
import pandas as pd
import time
import asyncio
import signal
from pathlib import Path
import json
import yaml
from dotenv import load_dotenv
from py2neo import Graph, Node, Relationship
import networkx as nx
import shutil


# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')  # Adjust this path as needed
load_dotenv(dotenv_path=env_path)

celery = Celery('tasks', broker=os.getenv('CELERY_BROKER_URL'))

# Configure logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

def run_command(command):
    """Run a system command and log the output."""
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log.info(result.stdout.decode())
        log.error(result.stderr.decode())  # Use .error for stderr to distinguish error outputs
    except subprocess.CalledProcessError as e:
        log.error(f"Command failed: {e}")
        log.error(e.stdout.decode())
        log.error(e.stderr.decode())

@celery.task
def process_file(file_path):
    try:
        root = 'app'  # Define your root path
        run_id = time.strftime("%Y%m%d-%H%M%S")
        _enable_logging(root, run_id, verbose=True)
        progress_reporter = _get_progress_reporter("rich")

                # Ensure the 'input' directory exists
        input_dir = os.path.join(root, 'input')
        os.makedirs(input_dir, exist_ok=True)

        # Copy the uploaded file to the 'input' directory
        file_name = os.path.basename(file_path)
        input_file_path = os.path.join(input_dir, file_name)
        shutil.copy(file_path, input_file_path)
        log.info(f"Copied file to {input_file_path}")


        # Check if GraphRAG has already been initialized
        settings_path = os.path.join(root, 'settings.yaml')
        prompts_dir = os.path.join(root, 'prompts')

        def is_initialized():
            if not os.path.exists(prompts_dir) or not any(os.path.isfile(os.path.join(prompts_dir, f)) for f in os.listdir(prompts_dir)):
                return False
            return True

        if not is_initialized():
            log.info("Initializing GraphRAG...")
            init_command = f"python -m graphrag.index --init --root {root}"
            run_command(init_command)
        else:
            log.info("GraphRAG already initialized. Skipping initialization.")
            


        # Load the settings file
        with open(settings_path, 'r') as file:
            settings_data = yaml.safe_load(file)

        # Create GraphRAG config
        # pipeline_config, pipeline_config_dict, pipeline_config_json = create_graphrag_config(settings_data, root)
        # log.debug(f"PipelineConfig: {pipeline_config_json}")
        prompt_tune = f"python -m graphrag.prompt_tune --root {root}"
        run_command(prompt_tune)
        # Run indexing
        index_command = f"python -m graphrag.index --root {root}"
        run_command(index_command)

        # Convert Parquet to CSV and import into Neo4j
        convert_parquet_to_csv_and_import_to_neo4j()
    except Exception as e:
        log.error(f"Error in process_file: {e}")
        raise

@celery.task
def trigger_neo4j_import():
    convert_parquet_to_csv_and_import_to_neo4j()

def convert_parquet_to_csv_and_import_to_neo4j():
    base_output_dir = './app/output'
    csv_dir = '/neo4j-import'  # This should be the mounted volume path
    graph = Graph("bolt://neo4j:7687", auth=("neo4j", os.getenv('NEO4J_PASSWORD')))

    # Find the latest output directory by timestamp
    try:
        latest_dir = max([os.path.join(base_output_dir, d) for d in os.listdir(base_output_dir)], key=os.path.getmtime)
        parquet_dir = os.path.join(latest_dir, 'artifacts')
    except ValueError:
        log.error(f"No output directories found in {base_output_dir}")
        return

    log.info(f"Processing Parquet files from {parquet_dir}")

    # Check if there are any Parquet files
    if not os.path.exists(parquet_dir):
        log.error(f"Parquet directory {parquet_dir} does not exist.")
        return

    process_parquet_files(parquet_dir, graph)

def process_parquet_files(parquet_dir, graph):
    # Process each Parquet file
    for file_name in os.listdir(parquet_dir):
        if file_name.endswith('.parquet'):
            file_path = os.path.join(parquet_dir, file_name)
            log.info(f"Processing {file_name}")

            # Load the Parquet file into a DataFrame
            try:
                df = pd.read_parquet(file_path)
                if 'entity_graph' in df.columns:
                    # Handle GraphML data
                    process_graphml_data(df['entity_graph'])
                elif 'covariate_ids' in df.columns:
                    # Handle relationships
                    process_relationships(df, graph)
                elif 'description' in df.columns:
                    # Handle covariates
                    process_covariates(df, graph)
                elif 'chunk' in df.columns:
                    # Handle text units
                    process_text_units(df, graph)
                else:
                    log.info(f"Unknown data structure in {file_name}")
            except Exception as e:
                log.error(f"Error processing {file_name}: {e}")

def process_graphml_data(entity_graph_series):
    graph = Graph("bolt://neo4j:7687", auth=("neo4j", os.getenv('NEO4J_PASSWORD')))
    
    for graphml in entity_graph_series:
        try:
            # Parse GraphML data
            G = nx.parse_graphml(graphml)
            
            # Add nodes to Neo4j
            for node_id, node_data in G.nodes(data=True):
                node = Node("Entity", id=node_id, **node_data)
                graph.merge(node, "Entity", "id")
            
            # Add relationships to Neo4j
            for source, target, edge_data in G.edges(data=True):
                source_node = graph.nodes.match("Entity", id=source).first()
                target_node = graph.nodes.match("Entity", id=target).first()
                if source_node and target_node:
                    relationship = Relationship(source_node, "RELATED_TO", target_node, **edge_data)
                    graph.merge(relationship)
        
        except Exception as e:
            log.error(f"Error processing GraphML data: {e}")
            log.debug(f"GraphML data: {graphml}")

def process_relationships(df, graph):
    for _, row in df.iterrows():
        text_unit_id = row['text_unit_id']
        for covariate_id in row['covariate_ids']:
            # Create relationships in Neo4j
            query = """
            MATCH (t:TextUnit {id: $text_unit_id}), (c:Covariate {id: $covariate_id})
            MERGE (t)-[:RELATED_TO]->(c)
            """
            graph.run(query, text_unit_id=text_unit_id, covariate_id=covariate_id)

def process_covariates(df, graph):
    for _, row in df.iterrows():
        # Create or update Covariate nodes
        covariate = Node("Covariate", id=row['id'], description=row['description'])
        graph.merge(covariate, "Covariate", "id")

def process_text_units(df, graph):
    for _, row in df.iterrows():
        # Create or update TextUnit nodes
        text_unit = Node("TextUnit", id=row['id'], chunk=row['chunk'])
        graph.merge(text_unit, "TextUnit", "id")

def _enable_logging(root_dir, run_id, verbose):
    logging_file = os.path.join(root_dir, 'logs', f'{run_id}-indexing-engine.log')
    os.makedirs(os.path.dirname(logging_file), exist_ok=True)
    logging.basicConfig(
        filename=logging_file,
        filemode='a',
        format='%(asctime)s,%(msecs)d %(name)s %(level)s %(message)s',
        datefmt='%H:%M:%S',
        level=logging.DEBUG if verbose else logging.INFO,
    )

def _get_progress_reporter(reporter_type: str | None):
    if reporter_type is None or reporter_type == "rich":
        return RichProgressReporter("GraphRAG Indexer ")
    if reporter_type == "print":
        return PrintProgressReporter("GraphRAG Indexer ")
    if reporter_type == "none":
        return NullProgressReporter()
    raise ValueError(f"Invalid progress reporter type: {reporter_type}")

def redact(input_data: dict | BaseModel) -> str:
    """Sanitize the config JSON."""
    if isinstance(input_data, BaseModel):
        input_data = input_data.dict()  # Convert Pydantic model to dict

    def redact_dict(input_dict: dict) -> dict:
        if not isinstance(input_dict, dict):
            return input_dict

        result = {}
        for key, value in input_dict.items():
            if key in {
                "api_key",
                "connection_string",
                "container_name",
                "organization",
            }:
                if value is not None:
                    result[key] = f"REDACTED, length {len(value)}"
            elif isinstance(value, dict):
                result[key] = redact_dict(value)
            elif isinstance(value, list):
                result[key] = [redact_dict(i) for i in value]
            else:
                result[key] = value
        return result

    redacted_dict = redact_dict(input_data)
    return json.dumps(redacted_dict, indent=4)

def create_graphrag_config(data, root):
    """Convert the loaded configuration data into a usable PipelineConfig."""
    config = {
        'root_dir': root,
        'input': data.get('input'),
        'reporting': data.get('reporting'),
        'storage': data.get('storage'),
        'cache': data.get('cache'),
        'workflows': data.get('workflows', [])
    }
    pipeline_config = PipelineConfig(**config)

    # Serialize the PipelineConfig object to a dictionary
    pipeline_config_dict = pipeline_config.model_dump()

    # Optionally, serialize to JSON if needed
    pipeline_config_json = json.dumps(pipeline_config_dict, indent=4)
    
    # Return the PipelineConfig object, dict, or JSON string as needed
    return pipeline_config, pipeline_config_dict, pipeline_config_json
