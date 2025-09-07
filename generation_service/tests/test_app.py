from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "Generation Service running"}

def test_generate_valid_request(monkeypatch):
    # Mock generator.generate method to return fixed response
    class DummyGenerator:
        def generate(self, prompt):
            return "Generated response"

    monkeypatch.setattr("app.generator", DummyGenerator())

    payload = {
        "user_query": "Explain workflow",
        "context": [{"id": 1, "text": "Doc content"}]
    }
    response = client.post("/generate/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data

def test_generate_missing_fields():
    response = client.post("/generate/", json={})
    assert response.status_code == 422
