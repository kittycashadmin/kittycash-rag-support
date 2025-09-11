from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "Retrieval Service running"}

def test_search_missing_query():
    response = client.get("/search/")
    assert response.status_code == 422

def test_search_valid_query(monkeypatch):
    # Mock retriever.search to return a fixed response
    class DummyRetriever:
        def search(self, query):
            return [{"score": 0.9, "document": {"id": 1, "text": "Test doc"}}]

    monkeypatch.setattr("app.retriever", DummyRetriever())
    response = client.get("/search/", params={"query": "test"})
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "test"
    assert isinstance(data["results"], list)


