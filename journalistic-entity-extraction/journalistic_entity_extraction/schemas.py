from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str

class ProjectCreate(BaseModel):
    name: str

class DocumentCreate(BaseModel):
    filename: str
    path: str
    project_id: int
