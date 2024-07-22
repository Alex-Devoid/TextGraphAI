from fastapi.testclient import TestClient
from journalistic_entity_extraction.main import app

client = TestClient(app)

def test_register():
    response = client.post("/register/", json={"username": "testuser", "password": "testpass"})
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

def test_create_project():
    response = client.post("/projects/", json={"name": "Test Project"})
    assert response.status_code == 200
    assert response.json()["name"] == "Test Project"
