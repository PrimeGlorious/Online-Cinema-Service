import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from crud.genres import (
    get_genre_list_db,
    get_genre_by_id_db,
    create_genre_db,
    update_genre_db,
    delete_genre_db
)
from schemas.genres import GenreCreateSchema, GenreUpdateSchema
from database.models.movies import GenreModel

@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def sample_genre():
    return GenreModel(id=1, name="Action")

@pytest.mark.asyncio
async def test_get_genre_list_db_success(mock_db, sample_genre):
    # Mock the count query
    mock_db.execute.return_value.scalar.return_value = 1
    
    # Mock the select query
    mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_genre]
    
    genres, total = await get_genre_list_db(mock_db, page=1, per_page=10)
    
    assert len(genres) == 1
    assert total == 1
    assert genres[0].name == "Action"

@pytest.mark.asyncio
async def test_get_genre_list_db_not_found(mock_db):
    mock_db.execute.return_value.scalar.return_value = 0
    
    with pytest.raises(HTTPException) as exc_info:
        await get_genre_list_db(mock_db, page=1, per_page=10)
    
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "No genres found."

@pytest.mark.asyncio
async def test_get_genre_by_id_db_success(mock_db, sample_genre):
    mock_db.get.return_value = sample_genre
    
    genre = await get_genre_by_id_db(mock_db, 1)
    
    assert genre.id == 1
    assert genre.name == "Action"

@pytest.mark.asyncio
async def test_get_genre_by_id_db_not_found(mock_db):
    mock_db.get.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        await get_genre_by_id_db(mock_db, 1)
    
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Genre not found."

@pytest.mark.asyncio
async def test_create_genre_db_success(mock_db):
    genre_data = GenreCreateSchema(name="Comedy")
    mock_db.add = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    genre = await create_genre_db(mock_db, genre_data)
    
    assert genre.name == "Comedy"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

@pytest.mark.asyncio
async def test_update_genre_db_success(mock_db, sample_genre):
    mock_db.get.return_value = sample_genre
    update_data = GenreUpdateSchema(name="Adventure")
    
    updated_genre = await update_genre_db(mock_db, 1, update_data)
    
    assert updated_genre.name == "Adventure"
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

@pytest.mark.asyncio
async def test_update_genre_db_not_found(mock_db):
    mock_db.get.return_value = None
    update_data = GenreUpdateSchema(name="Adventure")
    
    with pytest.raises(HTTPException) as exc_info:
        await update_genre_db(mock_db, 1, update_data)
    
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Genre not found."

@pytest.mark.asyncio
async def test_delete_genre_db_success(mock_db, sample_genre):
    mock_db.get.return_value = sample_genre
    
    await delete_genre_db(mock_db, 1)
    
    mock_db.delete.assert_called_once_with(sample_genre)
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_delete_genre_db_not_found(mock_db):
    mock_db.get.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        await delete_genre_db(mock_db, 1)
    
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Genre not found." 