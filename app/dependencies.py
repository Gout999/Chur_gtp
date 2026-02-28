"""FastAPI dependency helpers."""
from typing import Dict


def get_request_context() -> Dict[str, str]:
    return {"source": "api"}
