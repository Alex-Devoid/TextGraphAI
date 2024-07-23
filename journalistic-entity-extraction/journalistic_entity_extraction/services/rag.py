import openai
import os
from .retrieval import retrieve_relevant_information

def generate_response(graph: Graph, user_query: str):
    # Retrieve relevant information from the knowledge graph
    relevant_info = retrieve_relevant_information(graph, user_query)
    
    # Convert relevant information to a string format
    context = " ".join([str(info['n']) for info in relevant_info])
    
    # Use OpenAI API to generate a response
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.Completion.create(
        engine="davinci",
        prompt=f"Context: {context}\n\nUser Query: {user_query}\n\nResponse:",
        max_tokens=150
    )
    return response.choices[0].text
