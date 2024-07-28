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
