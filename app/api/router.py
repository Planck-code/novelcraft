from fastapi import APIRouter

from app.api.v1 import chapters, memory, novels, tasks, visualization


api_router = APIRouter()
api_router.include_router(novels.router, prefix='/api/v1/novels', tags=['novels'])
api_router.include_router(chapters.router, prefix='/api/v1', tags=['chapters'])
api_router.include_router(tasks.router, prefix='/api/v1/tasks', tags=['tasks'])
api_router.include_router(memory.router, prefix='/api/v1', tags=['memory'])
api_router.include_router(visualization.router, prefix='/api/v1/novels', tags=['visualization'])
