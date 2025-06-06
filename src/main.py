from fastapi import FastAPI

from custom.logger import setup_logger
from routes.movies import router as movies_router


setup_logger()

app = FastAPI(
    title="Online Cinema Service",
    description="Description of project"
)

api_version_prefix = "/api/v1"

app.include_router(movies_router, prefix=f"{api_version_prefix}/theater", tags=["theater"])
