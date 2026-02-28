#!/usr/bin/env python3
"""
Upload an image to the homework marker API and print the full response.

Usage (run from Chur_gtp directory):
  python scripts/test_homework_upload.py path/to/image.png
  python scripts/test_homework_upload.py path/to/homework.jpg --subject "Mathematics" --max-score 100

Requires MINIMAX_API_KEY (and optionally MINIMAX_GROUP_ID) in .env or environment.
Uses the FastAPI TestClient so no server needs to be running.
"""
import argparse
import json
import sys
from pathlib import Path

# Run from Chur_gtp so config and app resolve
if __name__ == "__main__":
    _root = Path(__file__).resolve().parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

from fastapi.testclient import TestClient

from app.main import app

ALLOWED = (".png", ".jpg", ".jpeg")


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload image to homework marker API and print response")
    parser.add_argument("image", type=Path, help="Path to PNG, JPG, or JPEG image")
    parser.add_argument("--subject", type=str, default=None, help="Subject, e.g. Mathematics")
    parser.add_argument("--rubric", type=str, default=None, help="Marking criteria for the model")
    parser.add_argument("--max-score", type=int, default=100, help="Maximum score (default 100)")
    args = parser.parse_args()

    path = args.image.resolve()
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    if path.suffix.lower() not in ALLOWED:
        print(f"Error: allowed extensions are {ALLOWED}", file=sys.stderr)
        sys.exit(1)

    raw = path.read_bytes()
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"

    client = TestClient(app)
    data = {"max_score": str(args.max_score)}
    if args.subject:
        data["subject"] = args.subject
    if args.rubric:
        data["rubric"] = args.rubric

    resp = client.post(
        "/api/v1/homework/mark",
        files={"file": (path.name, raw, mime)},
        data=data,
    )

    print(f"Status: {resp.status_code}")
    print()
    try:
        body = resp.json()
        print(json.dumps(body, indent=2, ensure_ascii=False))
    except Exception:
        print(resp.text)

    if resp.status_code != 200:
        sys.exit(1)


if __name__ == "__main__":
    main()
