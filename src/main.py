from fastapi import FastAPI, Request, HTTPException
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from custom.logger import setup_logger
from routes.carts import router as carts_router
from routes.movies import router as movies_router
from routes.orders import router as orders_router
from routes.payments import router as payments_router


setup_logger()

app = FastAPI(
    title="Online Cinema Service",
    description="Description of project"
)

limiter = Limiter(key_func=get_remote_address)


@app.exception_handler(RateLimitExceeded)
async def ratelimit_error(request: Request, exc: RateLimitExceeded):
    return HTTPException(status_code=429, detail="Too many requests, please try again later.")


api_version_prefix = "/api/v1"

app.include_router(movies_router, prefix=f"{api_version_prefix}/theater", tags=["theater"])
app.include_router(orders_router, prefix=f"{api_version_prefix}/theater", tags=["theater"])
app.include_router(payments_router, prefix=f"{api_version_prefix}/theater", tags=["theater"])
app.include_router(carts_router, prefix=f"{api_version_prefix}/cart", tags=["theater"])
