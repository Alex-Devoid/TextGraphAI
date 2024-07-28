import os
import re
import json
import argparse
import spacy
import openai
from textgraphai.utils.process_text import extract_text_from_pdfs

nlp = spacy.load("en_core_web_sm")

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\[.*?\]', '', text)
    text = text.strip()
    return text

def chunk_text(text, chunk_size=600):
    words = text.split()
    for i in range(0, len(words), chunk_size):
        yield ' '.join(words[i:i+chunk_size])

def extract_entities(text):
    doc = nlp(text)
    entities = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]
    return entities

def extract_relationships(text, api_key):
    openai.api_key = api_key
    response = openai.Completion.create(
        engine="davinci",
        prompt=f"Extract relationships from the following text:\n\n{text}",
        max_tokens=1000
    )
    return response.choices[0].text

def preprocess_file(input_file, output_dir, chunk_size=600, api_key=None):
    with open(input_file, 'r') as file:
        text = file.read()
    
    cleaned_text = clean_text(text)
    chunks = list(chunk_text(cleaned_text, chunk_size))

    for i, chunk in enumerate(chunks):
        entities = extract_entities(chunk)
        relationships = extract_relationships(chunk, api_key)

        output_data = {
            'chunk': chunk,
            'entities': entities,
            'relationships': json.loads(relationships)
        }

        output_file = os.path.join(output_dir, f"{os.path.basename(input_file)}_chunk_{i}.json")
        with open(output_file, 'w') as chunk_file:
            json.dump(output_data, chunk_file, indent=4)

def preprocess_directory(input_dir, output_dir, chunk_size=600, api_key=None):
    for filename in os.listdir(input_dir):
        if filename.endswith(".txt"):
            preprocess_file(os.path.join(input_dir, filename), output_dir, chunk_size, api_key)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Preprocess text data.')
    parser.add_argument('--input', required=True, help='Input file or directory')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--chunk_size', type=int, default=600, help='Chunk size for text segmentation')
    parser.add_argument('--api_key', required=True, help='OpenAI API Key for relationship extraction')
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    if os.path.isfile(args.input):
        preprocess_file(args.input, args.output, args.chunk_size, args.api_key)
    elif os.path.isdir(args.input):
        preprocess_directory(args.input, args.output, args.chunk_size, args.api_key)
    else:
        raise ValueError("Invalid input path. Must be a file or directory.")
