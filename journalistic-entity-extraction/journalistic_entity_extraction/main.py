import os
from fastapi import FastAPI, Depends, UploadFile, File
from sqlalchemy.orm import Session
from . import crud, models, schemas
from .database import SessionLocal, engine
from .services.entity_extraction import extract_entities_from_text
from .services.knowledge_graph import build_knowledge_graph
from py2neo import Graph
from dotenv import load_dotenv

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

@app.post("/register/", response_model=schemas.UserCreate)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.create_user(db=db, user=user)
    return db_user

@app.post("/projects/", response_model=schemas.ProjectCreate)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    return crud.create_project(db=db, project=project)

@app.post("/projects/{project_id}/documents/")
def upload_document(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_location = f"files/{project_id}/{file.filename}"
    os.makedirs(os.path.dirname(file_location), exist_ok=True)
    with open(file_location, "wb") as f:
        f.write(file.file.read())
    db_document = crud.create_document(db=db, document=schemas.DocumentCreate(
        filename=file.filename, path=file_location, project_id=project_id))
    return db_document

@app.post("/projects/{project_id}/extract_entities/")
def extract_entities(project_id: int, db: Session = Depends(get_db), graph: Graph = Depends(get_neo4j)):
    documents = db.query(models.Document).filter(models.Document.project_id == project_id).all()
    entities = []
    for doc in documents:
        with open(doc.path, "r") as f:
            text = f.read()
            entities.extend(extract_entities_from_text(text))
    knowledge_graph = build_knowledge_graph(graph, entities)
    return {"entities": entities, "knowledge_graph": knowledge_graph}
