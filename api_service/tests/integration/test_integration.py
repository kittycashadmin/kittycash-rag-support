import pytest
import httpx
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app import app

client = TestClient(app)

mock_retrieval_response = {
    "results": [
        {"score": 0.95, "document": {"id": 1, "text": "Sample doc text"}}
    ]
}

mock_generation_response = {
    "answer": "This is a generated answer."
}

@patch("httpx.AsyncClient.get")
@patch("httpx.AsyncClient.post")
def test_full_query_flow(mock_post, mock_get):
    # Mock retrieval service GET response
    mock_get.return_value = MagicMock()
    mock_get.return_value.json.return_value = mock_retrieval_response
    mock_get.return_value.raise_for_status = lambda: None

    # Mock generation service POST response
    mock_post.return_value = MagicMock()
    mock_post.return_value.json.return_value = mock_generation_response
    mock_post.return_value.raise_for_status = lambda: None

    response = client.post("/query/", json={"user_query": "Sample query"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["answer"] == mock_generation_response["answer"]


@patch("httpx.AsyncClient.get")
@patch("httpx.AsyncClient.post")
def test_retrieval_service_failure(mock_post, mock_get):
    dummy_request = httpx.Request("GET", "http://retrieval-service/search")
    mock_get.side_effect = httpx.RequestError("Retrieval service down", request=dummy_request)
    mock_post.return_value = MagicMock()

    response = client.post("/query/", json={"user_query": "Test failure"})
    assert response.status_code == 503
    assert "Service unavailable" in response.json()["detail"]


@patch("httpx.AsyncClient.get")
@patch("httpx.AsyncClient.post")
def test_generation_service_failure(mock_post, mock_get):
    # Retrieval service OK
    mock_get.return_value = MagicMock()
    mock_get.return_value.json.return_value = mock_retrieval_response
    mock_get.return_value.raise_for_status = lambda: None

    # Generation service fails
    dummy_request = httpx.Request("POST", "http://generation-service/generate")
    mock_post.side_effect = httpx.RequestError("Generation service error", request=dummy_request)

    response = client.post("/query/", json={"user_query": "Test generation failure"})
    assert response.status_code == 503
    assert "Service unavailable" in response.json()["detail"]

