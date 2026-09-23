"""
main.py - Root Entrypoint for Render and Cloud ASGI Deployments
Directly exposes FastAPI 'app' from backend.main so that both:
- uvicorn main:app
- uvicorn backend.main:app
work interchangeably in any cloud deployment environment.
"""

import os
import sys

# Ensure backend directory and root are in sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(root_dir, "backend")

for p in [root_dir, backend_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.main import app  # noqa: F401

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port)
