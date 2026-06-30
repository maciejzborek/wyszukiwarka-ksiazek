import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version():
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert isinstance(data["version"], str)


def test_search_missing_title():
    response = client.get("/search")
    assert response.status_code == 422  # Unprocessable Entity – title is required


def test_search_limit_too_high():
    response = client.get("/search?title=Python&limit=100")
    assert response.status_code == 422


def test_search_returns_results():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "numFound": 2,
        "docs": [
            {
                "title": "Clean Code",
                "author_name": ["Robert C. Martin"],
                "first_publish_year": 2008,
                "isbn": ["9780132350884"],
                "key": "/works/OL123W",
            },
            {
                "title": "Clean Architecture",
                "author_name": ["Robert C. Martin"],
                "first_publish_year": 2017,
                "isbn": ["9780134494166"],
                "key": "/works/OL456W",
            },
        ],
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

        response = client.get("/search?title=Clean+Code&limit=2")

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "Clean Code"
    assert data["total_found"] == 2
    assert len(data["results"]) == 2
    assert data["results"][0]["title"] == "Clean Code"
    assert "Robert C. Martin" in data["results"][0]["authors"]


def test_search_empty_results():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"numFound": 0, "docs": []}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

        response = client.get("/search?title=xyznonexistentbookxyz")

    assert response.status_code == 200
    data = response.json()
    assert data["total_found"] == 0
    assert data["results"] == []
