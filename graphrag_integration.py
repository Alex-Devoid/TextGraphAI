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
            file_pattern=".*\.txt$",
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
