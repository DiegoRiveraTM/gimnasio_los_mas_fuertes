from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.limiter import limiter
from app.core.redis_client import close_redis_client
from app.routes.qr import router as qr_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis_client()


app = FastAPI(
    title="QR Code Service",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174",
],
    allow_credentials = True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],    
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

Instrumentator().instrument(app).expose(app)

app.include_router(qr_router, prefix="/qr", tags=["qr"])


@app.get("/")
def server_running():
    return {"message": "QR Code Service running on port 8002"}


@app.get("/health")
def health_check():
    return {"message": "health check working correctly"}