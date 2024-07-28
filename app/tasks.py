from celery import Celery
from graphrag.index import PipelineConfig, run_pipeline_with_config
from graphrag.index.progress import RichProgressReporter
import pandas as pd
import os
import time
import logging
import asyncio
import signal
from py2neo import Graph

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

    # Convert Parquet to CSV and import into Neo4j
    convert_parquet_to_csv_and_import_to_neo4j()

def convert_parquet_to_csv_and_import_to_neo4j():
    # Parquet to CSV conversion
    parquet_dir = './inputs/artifacts'
    csv_dir = './neo4j-import'

    def clean_quotes(value):
        if isinstance(value, str):
            value = value.strip().replace('""', '"').replace('"', '')
            if ',' in value or '"' in value:
                value = f'"{value}"'
        return value

    for file_name in os.listdir(parquet_dir):
        if file_name.endswith('.parquet'):
            parquet_file = os.path.join(parquet_dir, file_name)
            csv_file = os.path.join(csv_dir, file_name.replace('.parquet', '.csv'))

            df = pd.read_parquet(parquet_file)
            for column in df.select_dtypes(include=['object']).columns:
                df[column] = df[column].apply(clean_quotes)

            df.to_csv(csv_file, index=False, quoting=csv.QUOTE_NONNUMERIC)
            print(f"Converted {parquet_file} to {csv_file} successfully.")

    print("All Parquet files have been converted to CSV.")

    # Import CSVs into Neo4j
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "password"))  # Update with your Neo4j credentials

    # Load CSV and create nodes and relationships
    graph.run("""
    // Add the Cypher commands from your provided script here
    """)

