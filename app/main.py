"""FastAPI entrypoint for ChurGPT backend."""
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.database import engine, Base

# Create database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ChurGPT API",
    description="Backend API for ChurGPT - Intelligent Learning Platform",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict:
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "ChurGPT API",
        "version": "1.0.0"
    }


@app.get("/")
def root() -> dict:
    """Root endpoint."""
    return {
        "message": "Welcome to ChurGPT API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.middleware("http")
async def teacher_api_envelope(request, call_next):
    """Middleware to wrap teacher API responses in standardized format."""
    response = await call_next(request)
    
    if not request.url.path.startswith("/api/v1/teachers"):
        return response

    content_type = response.headers.get("content-type", "")
    if "application/json" not in content_type:
        return response

    body = b""
    async for chunk in response.body_iterator:
        body += chunk

    if not body:
        payload = None
    else:
        payload = json.loads(body.decode("utf-8"))

    if isinstance(payload, dict) and "success" in payload and ("data" in payload or "error" in payload):
        wrapped = payload
    elif response.status_code < 400:
        wrapped = {"success": True, "data": payload}
    else:
        wrapped = {"success": False, "error": payload}

    headers = dict(response.headers)
    headers.pop("content-length", None)
    return JSONResponse(status_code=response.status_code, content=wrapped, headers=headers)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
