"""
EduGuide configuration.
Load from .env; used by graph, memory, and tools.
"""
import os
from pathlib import Path

# Load from .env if present (e.g. via python-dotenv)
_ENV = os.environ

# API keys and LLM config (set in .env)
OPENAI_API_KEY = _ENV.get("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = _ENV.get("ANTHROPIC_API_KEY", "")

# Optional: project root
PROJECT_ROOT = Path(__file__).resolve().parent
