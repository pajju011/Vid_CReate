from fastapi import APIRouter
from app.api.routes import projects, uploads, generation, videos, clips, rendering, jobs, providers

api_router = APIRouter()

api_router.include_router(projects.router)
api_router.include_router(uploads.router)
api_router.include_router(generation.router)
api_router.include_router(videos.router)
api_router.include_router(clips.router)
api_router.include_router(rendering.router)
api_router.include_router(jobs.router)
api_router.include_router(providers.router)

