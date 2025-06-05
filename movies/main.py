from fastapi import FastAPI
from movies.api.endpoints import genres, stars, directors, movies

app = FastAPI(title="Online Cinema - Movies App")

app.include_router(genres.router)
app.include_router(stars.router)
app.include_router(directors.router)
app.include_router(movies.router)
