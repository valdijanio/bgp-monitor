#!/usr/bin/env python3
"""
Entry point para o BGP Monitor.
"""
import uvicorn
from app.core.config import settings


def main():
    """Inicia o servidor FastAPI."""
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
