"""
Main entry point for running the API server.

Usage:
    python -m src.api.main
    
    Or with uvicorn:
    uvicorn src.api.main:app --host 0.0.0.0 --port 8000
"""

import uvicorn
from .api_server import app

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

