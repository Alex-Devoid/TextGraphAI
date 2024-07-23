from fastapi import FastAPI, Depends, UploadFile, File
from sqlalchemy.orm import Session
from . import crud, models, schemas
from .database import SessionLocal, engine
from .services.rag import generate_response
from py2neo import Graph
from dotenv import load_dotenv
import os

load_dotenv()

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_neo4j():
    graph = Graph(
        os.getenv("NEO4J_URI", "bolt://neo4j:7687"),
        auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "test"))
    )
    return graph

@app.post("/rag/")
async def rag_endpoint(user_query: str, graph: Graph = Depends(get_neo4j)):
    response = generate_response(graph, user_query)
    return {"response": response}

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_location = f"files/{file.filename}"
    with open(file_location, "wb") as f:
        f.write(file.file.read())
    return {"info": f"file '{file.filename}' saved at '{file_location}'"}
