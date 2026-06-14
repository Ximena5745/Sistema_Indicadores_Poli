from fastapi import APIRouter

from app.api.v1.endpoints import auth, cmi, dashboard, health, indicators, om

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(indicators.router, prefix="/indicators", tags=["indicators"])
api_router.include_router(cmi.router, prefix="/cmi", tags=["cmi"])
api_router.include_router(om.router, prefix="/om", tags=["om"])
