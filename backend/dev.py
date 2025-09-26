#!/usr/bin/env python3

import uvicorn
from config.settings import settings

if __name__ == "__main__":
    print("Starting Nala Health Coach API in development mode...")
    print(f"API will be available at http://{settings.api_host}:{settings.api_port}")
    print(f"API documentation at http://{settings.api_host}:{settings.api_port}/docs")

    uvicorn.run(
        "app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower(),
        access_log=True
    )