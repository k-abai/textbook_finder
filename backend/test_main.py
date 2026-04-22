from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get('/health')

    assert response.status_code == 200
    payload = response.json()
    assert payload['ok'] is True
    assert payload['service'] == 'TextbookFinder API'


def test_search_endpoint_returns_limited_results() -> None:
    response = client.post('/search', json={'query': 'Calculus', 'limit': 3})

    assert response.status_code == 200
    payload = response.json()
    assert payload['ok'] is True
    assert payload['query'] == 'Calculus'
    assert len(payload['results']) == 3


def test_search_validation_error_shape() -> None:
    response = client.post('/search', json={'query': ''})

    assert response.status_code == 422
    payload = response.json()
    assert payload['ok'] is False
    assert payload['error']['code'] == 'VALIDATION_ERROR'
