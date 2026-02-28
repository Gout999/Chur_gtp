"""FastAPI entrypoint for local development and Docker runtime."""
from fastapi import FastAPI

from app.api.v1 import api_router

app = FastAPI(title="EduGuide API", version="0.1.0")
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
