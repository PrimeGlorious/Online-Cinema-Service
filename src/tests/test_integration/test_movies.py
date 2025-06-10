import pytest
from loguru import logger


@pytest.mark.asyncio
async def test_create_movie_success(async_client):
    payload = {
        "name": "The Shawshank Redemption",
        "year": 1994,
        "time": 142,
        "imdb": 9.3,
        "votes": 2500000,
        "meta_score": 80.0,
        "gross": 28341469.00,
        "description": "Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.",
        "price": 12.99,
        "genres": ["Drama"],
        "certification": "20250610",
        "stars": ["Pitt"],
        "directors": ["Tarantino"],
    }

    response = await async_client.post("/api/v1/theater/movies/", json=payload)

    assert response.status_code == 201 or response.status_code == 409
    data = response.json()
    if response.status_code == 201:
        assert data["name"] == payload["name"]
        assert data["year"] == payload["year"]


@pytest.mark.asyncio
async def test_create_movie_missing_field(async_client):
    payload = {
        "name": "Testing movie 20250610",
        "description": "20250610",
        "year": 2010,
        "uuid": 20250610,
        "certification": "20250610",
        "time": 111,
        "imdb": 22,
        "votes": 1111,
        "meta_score": 22,
        "gross": 33,
        "price": 33,
    }

    response = await async_client.post("/api/v1/theater/movies/", json=payload)

    assert response.status_code == 422
