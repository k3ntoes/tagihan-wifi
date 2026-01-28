"""
API v1 router - Main API entry point for all endpoints
"""

from fastapi import APIRouter

# Import endpoint routers
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.billing import router as billing_router
from app.api.v1.endpoints.customers import router as customers_router
from app.api.v1.endpoints.payments import router as payments_router

# Initialize main router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth_router)
api_router.include_router(customers_router)
api_router.include_router(payments_router)
api_router.include_router(billing_router)
