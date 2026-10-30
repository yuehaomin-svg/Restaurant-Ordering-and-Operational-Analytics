from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routers import analytics, menu, orders

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")
app.include_router(menu.router)
app.include_router(orders.router)
app.include_router(analytics.router)

frontend_path = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=frontend_path), name="static")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": settings.app_name}


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(frontend_path / "index.html")
