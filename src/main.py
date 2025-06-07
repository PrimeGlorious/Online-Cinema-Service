from fastapi import FastAPI

from custom.logger import setup_logger
from routes.movies import router as movies_router
from routes.carts import router as carts_router


setup_logger()

app = FastAPI(
    title="Movies homework",
    description="Description of project"
)

api_version_prefix = "/api/v1"

app.include_router(movies_router, prefix=f"{api_version_prefix}/theater", tags=["theater"])
app.include_router(carts_router, prefix=f"{api_version_prefix}/cart", tags=["theater"])