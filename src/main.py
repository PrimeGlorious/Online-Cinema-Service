from fastapi import FastAPI, Request, HTTPException
from fastapi.openapi.utils import get_openapi
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from custom.logger import setup_logger
from routes.carts import router as carts_router
from routes.movies import router as movies_router
from routes.genres import router as genres_router
from routes.stars import router as stars_router
from routes.accounts import router as accounts_router
from routes.orders import router as orders_router
from routes.payments import router as payments_router
from routes.comments import router as comments_router


setup_logger()

app = FastAPI(
    title="Online Cinema Service",
    description="Description of project"
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Your API",
        version="1.0.0",
        description="API with JWT auth in Swagger",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method.setdefault("security", [{"BearerAuth": []}])
    app.openapi_schema = openapi_schema
    return openapi_schema


app.openapi = custom_openapi

limiter = Limiter(key_func=get_remote_address)


@app.exception_handler(RateLimitExceeded)
async def ratelimit_error(request: Request, exc: RateLimitExceeded):
    return HTTPException(status_code=429, detail="Too many requests, please try again later.")


api_version_prefix = "/api/v1"

app.include_router(movies_router, prefix=f"{api_version_prefix}/theater", tags=["Movies"])
app.include_router(comments_router, prefix=f"{api_version_prefix}/comments", tags=["Comments"])
app.include_router(stars_router, prefix=f"{api_version_prefix}/theater", tags=["Stars"])
app.include_router(genres_router, prefix=f"{api_version_prefix}/theater", tags=["Genres"])
app.include_router(accounts_router, prefix=f"{api_version_prefix}/accounts", tags=["Accounts"])
app.include_router(orders_router, prefix=f"{api_version_prefix}/theater", tags=["Orders"])
app.include_router(payments_router, prefix=f"{api_version_prefix}/theater", tags=["Payments"])
app.include_router(carts_router, prefix=f"{api_version_prefix}/theater", tags=["Carts"])
