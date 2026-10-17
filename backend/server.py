"""Compatibility launcher: the authoritative backend is backend.main:app.

Run from the repository root with `uv run --locked python -m backend.server`.
"""
from pathlib import Path
import sys

if __name__ == "__main__":
    # Also support the previous `python backend/server.py` invocation.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000)
