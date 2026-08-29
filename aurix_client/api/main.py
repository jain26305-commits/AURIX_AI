from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import (
    auth_router,
    data_router,
    inventory_router,
    alerts_router,
    case_router,
    procurement_router,
    manufacturing_router,
    fulfillment_router,
    returns_router,
    query_router,
    admin_router
)

app = FastAPI(
    title="AURIX Enterprise Intelligence Engine",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API routers under /api/v1
app.include_router(auth_router.router, prefix="/api/v1")
app.include_router(data_router.router, prefix="/api/v1")
app.include_router(inventory_router.router, prefix="/api/v1")
app.include_router(alerts_router.router, prefix="/api/v1")
app.include_router(case_router.router, prefix="/api/v1")
app.include_router(procurement_router.router, prefix="/api/v1")
app.include_router(manufacturing_router.router, prefix="/api/v1")
app.include_router(fulfillment_router.router, prefix="/api/v1")
app.include_router(returns_router.router, prefix="/api/v1")
app.include_router(query_router.router, prefix="/api/v1")
app.include_router(admin_router.router, prefix="/api/v1")

@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "HEALTHY",
        "engine": "AURIX_ENTERPRISE_API",
        "version": "1.0.0",
        "routesMounted": len(app.routes)
    }