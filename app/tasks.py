import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

from celery import Celery
from graphrag.index import PipelineConfig, create_pipeline_config, run_pipeline_with_config
from graphrag.index.progress.rich import RichProgressReporter
from graphrag.index.progress import (
    NullProgressReporter,
    PrintProgressReporter,
    ProgressReporter,
)
from graphrag.index.cache import NoopPipelineCache
import pandas as pd
import os
import time
import logging
import asyncio
import signal
from py2neo import Graph
from pathlib import Path
import json
import yaml

celery = Celery('tasks', broker='pyamqp://guest@localhost//')


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def _enable_logging(root_dir, run_id, verbose):
    logging_file = os.path.join(root_dir, 'logs', f'{run_id}-indexing-engine.log')
    os.makedirs(os.path.dirname(logging_file), exist_ok=True)
    logging.basicConfig(
        filename=logging_file,
        filemode='a',
        format='%(asctime)s,%(msecs)d %(name)s %(levellevel)s %(message)s',
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

def _create_default_config(root, config_path, verbose, dryrun, progress_reporter):
    # Create or load configuration
    parameters = _read_config_parameters(root, config_path, progress_reporter)
    redacted_parameters = redact(parameters)  # Redact sensitive information
    log.info("using default configuration: %s", redacted_parameters)
    if verbose or dryrun:
        progress_reporter.info(f"Using default configuration: {redacted_parameters}")
    result = create_pipeline_config(parameters, verbose)
    redacted_result = redact(result.model_dump())  # Redact and serialize to dict
    if verbose or dryrun:
        progress_reporter.info(f"Final Config: {redacted_result}")
    if dryrun:
        progress_reporter.info("dry run complete, exiting...")
        sys.exit(0)
    return result

def _read_config_parameters(root, config, reporter):
    root_path = Path(root)
    settings_yaml = Path(config) if config and Path(config).suffix in [".yaml", ".yml"] else root_path / "settings.yaml"
    if not settings_yaml.exists():
        settings_yaml = root_path / "settings.yml"
    settings_json = Path(config) if config and Path(config).suffix == ".json" else root_path / "settings.json"

    if settings_yaml.exists():
        reporter.success(f"Reading settings from {settings_yaml}")
        with settings_yaml.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
            return create_graphrag_config(data, root)[0]  # Return the PipelineConfig object

    if settings_json.exists():
        reporter.success(f"Reading settings from {settings_json}")
        with settings_json.open("r", encoding="utf-8") as file:
            data = json.load(file)
            return create_graphrag_config(data, root)[0]  # Return the PipelineConfig object

    reporter.success("Reading settings from environment variables")
    return create_graphrag_config({}, root)[0]

@celery.task
def process_file(file_path):
    root = 'app'  # Define your root path
    run_id = time.strftime("%Y%m%d-%H%M%S")
    _enable_logging(root, run_id, verbose=True)
    progress_reporter = _get_progress_reporter("rich")

    # Create or load the pipeline configuration
    pipeline_config = _create_default_config(
        root, config_path=os.path.join(root, 'settings.yaml'), verbose=True, dryrun=False, progress_reporter=progress_reporter
    )
    cache = NoopPipelineCache()  # No caching in this example

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

def redact(input: dict) -> str:
    """Sanitize the config json."""

    def redact_dict(input: dict) -> dict:
        if not isinstance(input, dict):
            return input

        result = {}
        for key, value in input.items():
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

    redacted_dict = redact_dict(input)
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