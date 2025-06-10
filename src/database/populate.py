import asyncio
import math
from typing import List, Dict, Tuple
import uuid

import pandas as pd
import numpy as np
from sqlalchemy import insert, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from tqdm import tqdm

from config import get_settings
from database import (
    GenreModel,
    StarModel,
    DirectorModel,
    CertificationModel,
    MovieModel,
    MovieGenreModel,
    MovieStarModel,
    MovieDirectorModel,
)
from database import get_db_contextmanager

CHUNK_SIZE = 1000


class CSVDatabaseSeeder:
    def __init__(self, csv_file_path: str, db_session: AsyncSession) -> None:
        self._csv_file_path = csv_file_path
        self._db_session = db_session

    async def is_db_populated(self) -> bool:
        result = await self._db_session.execute(select(MovieModel).limit(1))
        return result.scalars().first() is not None

    def _preprocess_csv(self) -> pd.DataFrame:
        data = pd.read_csv(self._csv_file_path)
        data = data.drop_duplicates(subset=['name', 'year'], keep='first')
        for col in ['genres', 'stars', 'directors']:
            data[col] = data[col].fillna('').astype(str)
        data['description'] = data['description'].fillna('No description')
        data['meta_score'] = data['meta_score'].where(pd.notnull(data['meta_score']), None)
        data['gross'] = data['gross'].where(pd.notnull(data['gross']), None)
        return data

    async def _get_or_create_bulk(self, model, items: List[str], unique_field: str) -> Dict[str, object]:
        existing_dict: Dict[str, object] = {}
        if items:
            for i in range(0, len(items), CHUNK_SIZE):
                chunk = items[i:i + CHUNK_SIZE]
                result = await self._db_session.execute(
                    select(model).where(getattr(model, unique_field).in_(chunk))
                )
                for obj in result.scalars().all():
                    existing_dict[getattr(obj, unique_field)] = obj
        new_items = [item for item in items if item not in existing_dict]
        new_records = [{unique_field: item} for item in new_items]
        if new_records:
            await self._db_session.execute(insert(model).values(new_records))
            await self._db_session.flush()
            for i in range(0, len(new_items), CHUNK_SIZE):
                chunk = new_items[i:i + CHUNK_SIZE]
                result_new = await self._db_session.execute(
                    select(model).where(getattr(model, unique_field).in_(chunk))
                )
                for obj in result_new.scalars().all():
                    existing_dict[getattr(obj, unique_field)] = obj
        return existing_dict

    def _prepare_movies_data(self, data: pd.DataFrame, cert_map: Dict[str, object]) -> List[Dict[str, object]]:
        movies_data = []
        for _, row in data.iterrows():
            movies_data.append({
                "uuid": str(uuid.uuid4()),
                "name": row['name'],
                "year": int(row['year']),
                "time": int(row['time']),
                "imdb": float(row['imdb']),
                "votes": int(row['votes']),
                "meta_score": float(row['meta_score']) if not pd.isna(row['meta_score']) else None,
                "gross": float(row['gross']) if not pd.isna(row['gross']) else None,
                "description": row['description'],
                "price": float(row['price']),
                "certification_id": cert_map[row['certification']].id
            })
        return movies_data

    def _prepare_associations(
        self,
        data: pd.DataFrame,
        movie_ids: List[int],
        genre_map: Dict[str, object],
        star_map: Dict[str, object],
        director_map: Dict[str, object]
    ) -> Tuple[List[Dict[str, int]], List[Dict[str, int]], List[Dict[str, int]]]:
        movie_genres, movie_stars, movie_directors = [], [], []
        for i, row in enumerate(data.itertuples(index=False)):
            movie_id = movie_ids[i]
            for genre in row.genres.split(','):
                genre = genre.strip()
                if genre:
                    movie_genres.append({"movie_id": movie_id, "genre_id": genre_map[genre].id})
            for star in row.stars.split(','):
                star = star.strip()
                if star:
                    movie_stars.append({"movie_id": movie_id, "star_id": star_map[star].id})
            for director in row.directors.split(','):
                director = director.strip()
                if director:
                    movie_directors.append({"movie_id": movie_id, "director_id": director_map[director].id})
        return movie_genres, movie_stars, movie_directors

    async def _bulk_insert(self, table, data_list: List[Dict[str, int]]) -> None:
        if not data_list:
            return
        for i in range(0, len(data_list), CHUNK_SIZE):
            chunk = data_list[i:i + CHUNK_SIZE]
            await self._db_session.execute(insert(table).values(chunk))
        await self._db_session.flush()

    async def seed(self) -> None:
        try:
            if self._db_session.in_transaction():
                await self._db_session.rollback()
            data = self._preprocess_csv()
            cert_map = await self._get_or_create_bulk(CertificationModel, list(data['certification'].unique()), 'name')
            genre_map = await self._get_or_create_bulk(GenreModel, list({g.strip() for s in data['genres'].dropna() for g in s.split(',')}), 'name')
            star_map = await self._get_or_create_bulk(StarModel, list({s.strip() for s in data['stars'].dropna() for s in s.split(',')}), 'name')
            director_map = await self._get_or_create_bulk(DirectorModel, list({d.strip() for d in data['directors'].dropna() for d in d.split(',')}), 'name')
            movies_data = self._prepare_movies_data(data, cert_map)
            result = await self._db_session.execute(insert(MovieModel).returning(MovieModel.id), movies_data)
            movie_ids = result.scalars().all()
            movie_genres, movie_stars, movie_directors = self._prepare_associations(data, movie_ids, genre_map, star_map, director_map)
            await self._bulk_insert(MovieGenreModel, movie_genres)
            await self._bulk_insert(MovieStarModel, movie_stars)
            await self._bulk_insert(MovieDirectorModel, movie_directors)
            await self._db_session.commit()
            print("Seeding completed.")
        except SQLAlchemyError as e:
            print(f"SQLAlchemy error: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise


async def main() -> None:
    settings = get_settings()
    async with get_db_contextmanager() as session:
        seeder = CSVDatabaseSeeder(settings.PATH_TO_MOVIES_CSV, session)
        if not await seeder.is_db_populated():
            await seeder.seed()
        else:
            print("DB already populated.")


if __name__ == "__main__":
    asyncio.run(main())
