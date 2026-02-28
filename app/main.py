"""FastAPI entrypoint for local development and Docker runtime."""
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router

app = FastAPI(title="EduGuide API", version="0.1.0")
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.middleware("http")
async def teacher_api_envelope(request, call_next):
    response = await call_next(request)
    if not request.url.path.startswith("/api/v1/teacher"):
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
