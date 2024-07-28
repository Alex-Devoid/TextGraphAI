import os
import asyncio
import pandas as pd
import openai 
from py2neo import Graph
from graphrag.index import run_pipeline, run_pipeline_with_config
from graphrag.index.config import PipelineCSVInputConfig, PipelineWorkflowReference
from graphrag.index.input import load_input
from graphrag.query import LocalSearch, GlobalSearch
from graphrag.query.context_builder import LocalSearchMixedContext, GlobalCommunityContext
from graphrag.query.indexer_adapters import read_indexer_entities, read_indexer_relationships, read_indexer_reports, read_indexer_text_units
from graphrag.vector_stores.lancedb import LanceDBVectorStore
from graphrag.query.llm.oai.chat_openai import ChatOpenAI
from graphrag.query.llm.oai.typing import OpenaiApiType
from graphrag.query.llm.oai.embedding import OpenAIEmbedding

def load_preprocessed_data(directory):
    data = []
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            with open(os.path.join(directory, filename), 'r') as file:
                data.append(json.load(file))
    return data

async def run_with_config(preprocessed_data, config_path):
    tables = []
    async for table in run_pipeline_with_config(config_or_path=config_path, dataset=preprocessed_data):
        tables.append(table)
    return tables

async def run_rag_pipeline(preprocessed_data, workflows):
    tables = []
    async for table in run_pipeline(dataset=preprocessed_data, workflows=workflows):
        tables.append(table)
    return tables

def run_rag(preprocessed_data_dir, config_path=None, workflows=None):
    preprocessed_data = load_preprocessed_data(preprocessed_data_dir)
    if config_path:
        return asyncio.run(run_with_config(preprocessed_data, config_path))
    elif workflows:
        return asyncio.run(run_rag_pipeline(preprocessed_data, workflows))
    else:
        raise ValueError("Either config_path or workflows must be provided.")

async def run_local_search(query, input_dir):
    # Load data from preprocessed files
    entity_df = pd.read_parquet(f"{input_dir}/create_final_nodes.parquet")
    entity_embedding_df = pd.read_parquet(f"{input_dir}/create_final_entities.parquet")
    text_unit_df = pd.read_parquet(f"{input_dir}/create_final_text_units.parquet")

    entities = read_indexer_entities(entity_df, entity_embedding_df)
    text_units = read_indexer_text_units(text_unit_df)

    context_builder = LocalSearchMixedContext(
        entities=entities,
        text_units=text_units,
        # Other context_builder parameters as needed
    )

    llm = ChatOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("GRAPHRAG_LLM_MODEL"),
        api_type=OpenaiApiType.OpenAI,
        max_retries=20,
    )

    search_engine = LocalSearch(
        llm=llm,
        context_builder=context_builder,
        # Other search_engine parameters as needed
    )

    result = await search_engine.asearch(query)
    return result.response

async def run_global_search(query, input_dir):
    # Load data from preprocessed files
    entity_df = pd.read_parquet(f"{input_dir}/create_final_nodes.parquet")
    entity_embedding_df = pd.read_parquet(f"{input_dir}/create_final_entities.parquet")
    report_df = pd.read_parquet(f"{input_dir}/create_final_community_reports.parquet")

    entities = read_indexer_entities(entity_df, entity_embedding_df)
    reports = read_indexer_reports(report_df, entity_df)

    context_builder = GlobalCommunityContext(
        community_reports=reports,
        entities=entities,
        # Other context_builder parameters as needed
    )

    llm = ChatOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("GRAPHRAG_LLM_MODEL"),
        api_type=OpenaiApiType.OpenAI,
        max_retries=20,
    )

    search_engine = GlobalSearch(
        llm=llm,
        context_builder=context_builder,
        # Other search_engine parameters as needed
    )

    result = await search_engine.asearch(query)
    return result.response

def run_local_search(preprocessed_data_dir, query):
    preprocessed_data = load_preprocessed_data(preprocessed_data_dir)
    return asyncio.run(run_local_search(query, preprocessed_data))

def run_global_search(preprocessed_data_dir, query):
    preprocessed_data = load_preprocessed_data(preprocessed_data_dir)
    return asyncio.run(run_global_search(query, preprocessed_data))

def connect_to_neo4j():
    graph = Graph(
        os.getenv("NEO4J_URI", "bolt://neo4j:7687"),
        auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "test"))
    )
    return graph

def get_knowledge_graph_data(graph, query):
    cypher_query = """
    MATCH (n)
    WHERE n.name CONTAINS $query
    RETURN n
    """
    results = graph.run(cypher_query, query=query).data()
    return results

def generate_response(graph, user_query):
    relevant_info = get_knowledge_graph_data(graph, user_query)
    context = " ".join([str(info['n']) for info in relevant_info])

    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.Completion.create(
        engine="davinci",
        prompt=f"Context: {context}\n\nUser Query: {user_query}\n\nResponse:",
        max_tokens=150
    )
    return response.choices[0].text
