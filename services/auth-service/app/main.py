from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.limiter import limiter
from app.routes.auth import router as auth_router

app = FastAPI(
    title="Gimnasio",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], #Change in production
    allow_credentials = True,
    allow_methods=["GET", "PUT", "DELETE", "POST"],
    allow_headers=["Authorization", "Content-Type"]
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    #response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
Instrumentator().instrument(app).expose(app)

app.include_router(auth_router, prefix="/auth", tags=["auth"])

@app.get('/')
def server_running():
    return {"message": "server running on port 8000"}

@app.get('/health')
def health_check():
    return {"message": "health check working correctly"}