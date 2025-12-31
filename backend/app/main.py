from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.logger import configure_logging
from app.repositories.neo4j_client import neo4j_client
from app.routers import attack_paths, assets, system

configure_logging()
settings = get_settings()

app = FastAPI(title="Attack Path Analysis Platform", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system.router)
app.include_router(attack_paths.router)
app.include_router(assets.router)


@app.on_event("shutdown")
async def shutdown_event():
    neo4j_client.close()


@app.get("/")
async def root():
    return {"status": "ok"}
