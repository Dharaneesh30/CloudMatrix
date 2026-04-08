from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from .api.routes_fastapi import router as api_router
    from .core.pipeline import initialize_storage
except ImportError:
    from api.routes_fastapi import router as api_router
    from core.pipeline import initialize_storage


app = FastAPI(title="CloudMatrix AI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    initialize_storage()


@app.get("/")
async def root() -> dict:
    return {"message": "CloudMatrix AI FastAPI backend is running"}


app.include_router(api_router)
