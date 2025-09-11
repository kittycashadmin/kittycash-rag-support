import pytest
import httpx
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "API Gateway running"}


def test_query_empty_payload():
    response = client.post("/query/", json={"user_query": ""})
    assert response.status_code == 400
    assert response.json()["detail"] == "user_query is required"


def test_query_success(mocker):
    mock_retrieval = mocker.MagicMock()
    mock_retrieval.json.return_value = {"results": [{"document": "Doc1"}]}
    mock_retrieval.raise_for_status = lambda: None

    mock_generation = mocker.MagicMock()
    mock_generation.json.return_value = {"answer": "Generated Answer"}
    mock_generation.raise_for_status = lambda: None

    mocker.patch("httpx.AsyncClient.get", return_value=mock_retrieval)
    mocker.patch("httpx.AsyncClient.post", return_value=mock_generation)

    response = client.post("/query/", json={"user_query": "What is KittyCash?"})
    assert response.status_code == 200
    assert response.json() == {"answer": "Generated Answer"}


def test_query_retrieval_service_unavailable(mocker):
    dummy_request = httpx.Request("GET", "http://retrieval-service/search")
    mocker.patch(
        "httpx.AsyncClient.get",
        side_effect=httpx.RequestError("Retrieval service down", request=dummy_request)
    )

    response = client.post("/query/", json={"user_query": "test"})
    assert response.status_code == 503
    assert "Service unavailable" in response.json()["detail"]
