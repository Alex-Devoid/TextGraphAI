import click
from textgraphai.utils.fetch_data import fetch_cspan_transcripts, fetch_bills
from textgraphai.utils.enhanced_preprocess import preprocess_directory
from textgraphai.services.rag import run_rag

@click.group()
def cli():
    pass

@cli.command()
@click.option('--api-key', prompt='ProPublica API Key', help='Your ProPublica API Key.')
@click.option('--neo4j-uri', prompt='Neo4j URI', help='The URI for your Neo4j instance.')
@click.option('--neo4j-user', prompt='Neo4j Username', help='Your Neo4j username.')
@click.option('--neo4j-password', prompt='Neo4j Password', help='Your Neo4j password.')
@click.option('--pdf-dir', prompt='PDF Directory', help='Directory containing PDF files.', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--output-dir', prompt='Output Directory', help='Directory to save preprocessed files.', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--config-path', prompt='Config Path', help='Path to the GraphRAG config file.', type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.option('--openai-api-key', prompt='OpenAI API Key', help='Your OpenAI API Key.')
def run(api_key, neo4j_uri, neo4j_user, neo4j_password, pdf_dir, output_dir, config_path, openai_api_key):
    transcripts = fetch_cspan_transcripts()
    bills = fetch_bills(api_key)
    
    pdf_files = [os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
    pdf_texts = extract_text_from_pdfs(pdf_files)
    
    all_texts = transcripts + bills + pdf_texts
    
    preprocess_directory(pdf_dir, output_dir, chunk_size=600, api_key=openai_api_key)
    
    run_rag(output_dir, config_path=config_path)

if __name__ == '__main__':
    cli()
