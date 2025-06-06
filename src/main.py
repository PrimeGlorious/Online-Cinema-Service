from fastapi import FastAPI

from custom.logger import setup_logger


setup_logger()

app = FastAPI(
    title="Movies homework",
    description="Description of project"
)
