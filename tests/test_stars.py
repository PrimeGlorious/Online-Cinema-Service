import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from crud.stars import (
    get_star_list_db,
    get_star_by_id_db,
    create_star_db,
    update_star_db,
    delete_star_db
)
from schemas.stars import StarCreateSchema, StarUpdateSchema
from database.models.movies import StarModel

@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def sample_star():
    return StarModel(
        id=1,
        name="John Doe",
        biography="A famous actor",
        birth_date="1990-01-01",
        photo_url="http://example.com/photo.jpg"
    )

@pytest.mark.asyncio
async def test_get_star_list_db_success(mock_db, sample_star):
    # Mock the count query
    mock_db.execute.return_value.scalar.return_value = 1
    
    # Mock the select query
    mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_star]
    
    stars, total = await get_star_list_db(mock_db, page=1, per_page=10)
    
    assert len(stars) == 1
    assert total == 1
    assert stars[0].name == "John Doe"

@pytest.mark.asyncio
async def test_get_star_list_db_not_found(mock_db):
    mock_db.execute.return_value.scalar.return_value = 0
    
    with pytest.raises(HTTPException) as exc_info:
        await get_star_list_db(mock_db, page=1, per_page=10)
    
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "No stars found."

@pytest.mark.asyncio
async def test_get_star_by_id_db_success(mock_db, sample_star):
    mock_db.get.return_value = sample_star
    
    star = await get_star_by_id_db(mock_db, 1)
    
    assert star.id == 1
    assert star.name == "John Doe"
    assert star.biography == "A famous actor"

@pytest.mark.asyncio
async def test_get_star_by_id_db_not_found(mock_db):
    mock_db.get.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        await get_star_by_id_db(mock_db, 1)
    
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Star not found."

@pytest.mark.asyncio
async def test_create_star_db_success(mock_db):
    star_data = StarCreateSchema(
        name="Jane Smith",
        biography="A talented actress",
        birth_date="1992-02-02",
        photo_url="http://example.com/jane.jpg"
    )
    mock_db.add = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    star = await create_star_db(mock_db, star_data)
    
    assert star.name == "Jane Smith"
    assert star.biography == "A talented actress"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

@pytest.mark.asyncio
async def test_update_star_db_success(mock_db, sample_star):
    mock_db.get.return_value = sample_star
    update_data = StarUpdateSchema(
        name="John Updated",
        biography="Updated biography"
    )
    
    updated_star = await update_star_db(mock_db, 1, update_data)
    
    assert updated_star.name == "John Updated"
    assert updated_star.biography == "Updated biography"
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

@pytest.mark.asyncio
async def test_update_star_db_not_found(mock_db):
    mock_db.get.return_value = None
    update_data = StarUpdateSchema(name="John Updated")
    
    with pytest.raises(HTTPException) as exc_info:
        await update_star_db(mock_db, 1, update_data)
    
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Star not found."

@pytest.mark.asyncio
async def test_delete_star_db_success(mock_db, sample_star):
    mock_db.get.return_value = sample_star
    
    await delete_star_db(mock_db, 1)
    
    mock_db.delete.assert_called_once_with(sample_star)
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_delete_star_db_not_found(mock_db):
    mock_db.get.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        await delete_star_db(mock_db, 1)
    
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Star not found." 