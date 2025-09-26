from fastapi import APIRouter
from datetime import datetime
import psutil
import os

health_router = APIRouter(prefix="/health", tags=["health"])

@health_router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Nala Health Coach API"
    }

@health_router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with system information"""
    try:
        memory_usage = psutil.virtual_memory()
        cpu_usage = psutil.cpu_percent(interval=1)

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "Nala Health Coach API",
            "system": {
                "cpu_usage_percent": cpu_usage,
                "memory_usage_percent": memory_usage.percent,
                "memory_available_mb": memory_usage.available / (1024 * 1024),
                "disk_usage": psutil.disk_usage('/').percent if os.path.exists('/') else "N/A"
            },
            "environment": {
                "python_version": f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}",
                "platform": psutil.platform.system()
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }