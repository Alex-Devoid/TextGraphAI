import openai
import os
import argparse
from dotenv import load_dotenv

load_dotenv()

def annotate_text(text):
    openai.api_key = os.getenv("OPENAI_API_KEY")

    response = openai.Completion.create(
        engine="davinci",
        prompt=f"Annotate the following text with entities and relationships:\n\n{text}",
        max_tokens=1000
    )

    return response.choices[0].text

def annotate_files(input_dir, output_dir):
    for filename in os.listdir(input_dir):
        if filename.endswith(".txt"):
            with open(os.path.join(input_dir, filename), 'r') as file:
                text = file.read()
            
            annotated_text = annotate_text(text)
            
            with open(os.path.join(output_dir, f"annotated_{filename}"), 'w') as output_file:
                output_file.write(annotated_text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Annotate text data with GPT-4.')
    parser.add_argument('--input', required=True, help='Input directory')
    parser.add_argument('--output', required=True, help='Output directory')
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    annotate_files(args.input, args.output)
