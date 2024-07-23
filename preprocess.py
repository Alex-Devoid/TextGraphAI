import os
import re
import argparse

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\[.*?\]', '', text)
    text = text.strip()
    return text

def chunk_text(text, chunk_size=600):
    words = text.split()
    for i in range(0, len(words), chunk_size):
        yield ' '.join(words[i:i+chunk_size])

def preprocess_file(input_file, output_dir, chunk_size=600):
    with open(input_file, 'r') as file:
        text = file.read()
    
    cleaned_text = clean_text(text)
    chunks = list(chunk_text(cleaned_text, chunk_size))

    for i, chunk in enumerate(chunks):
        with open(f"{output_dir}/{os.path.basename(input_file)}_chunk_{i}.txt", 'w') as chunk_file:
            chunk_file.write(chunk)

def preprocess_directory(input_dir, output_dir, chunk_size=600):
    for filename in os.listdir(input_dir):
        if filename.endswith(".txt"):
            preprocess_file(os.path.join(input_dir, filename), output_dir, chunk_size)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Preprocess text data.')
    parser.add_argument('--input', required=True, help='Input file or directory')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--chunk_size', type=int, default=600, help='Chunk size for text segmentation')
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    if os.path.isfile(args.input):
        preprocess_file(args.input, args.output, args.chunk_size)
    elif os.path.isdir(args.input):
        preprocess_directory(args.input, args.output, args.chunk_size)
    else:
        raise ValueError("Invalid input path. Must be a file or directory.")
