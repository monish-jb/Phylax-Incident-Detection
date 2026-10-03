import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.core.database import engine, Base, migrate_db
from backend.app.api import (
    auth, onboarding, contacts, cameras, incidents, alerts, reports, videos, dashboard
)
from backend.app.services.websocket_manager import manager

# Create DB tables & run migrations
Base.metadata.create_all(bind=engine)
migrate_db()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount /storage directory for thumbnails & posters
app.mount("/storage", StaticFiles(directory=settings.STORAGE_DIR), name="storage")

# Include Routers
app.include_router(auth.router)
app.include_router(onboarding.router)
app.include_router(contacts.router)
app.include_router(cameras.router)
app.include_router(incidents.router)
app.include_router(alerts.router)
app.include_router(reports.router)
app.include_router(videos.router)
app.include_router(dashboard.router)


@app.get("/api/health")
def health_check():
    return {
        "status": "ONLINE",
        "system": settings.PROJECT_NAME,
        "tagline": settings.TAGLINE,
        "version": settings.VERSION
    }


@app.websocket("/api/ws/jobs/{job_id}")
async def websocket_job_endpoint(websocket: WebSocket, job_id: int):
    await manager.connect(job_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(job_id, websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
