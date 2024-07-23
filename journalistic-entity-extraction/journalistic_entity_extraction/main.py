def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    return crud.create_project(db=db, project=project)

@app.post("/projects/{project_id}/documents/")
@app.post("/rag/")
async def rag_endpoint(user_query: str, graph: Graph = Depends(get_neo4j)):
    response = generate_response(graph, user_query)
    return {"response": response}

