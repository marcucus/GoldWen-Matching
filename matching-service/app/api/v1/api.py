from fastapi import APIRouter
from app.api.v1.endpoints import matching, users

api_router = APIRouter()
api_router.include_router(matching.router, prefix="/matching", tags=["matching"])
api_router.include_router(users.router, prefix="/users", tags=["users"])