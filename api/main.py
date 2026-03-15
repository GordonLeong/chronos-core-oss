# main.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio



# local import: db.init_db() is async and creates tables (db.py must exist)
from db import init_db

from routers.stocks import router as stocks_router
from routers.templates import router as templates_router
from routers.candidates import router as candidates_router


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chronos.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    App lifespan: run once before the app starts and once after its stops.
    Use this for async startup(init_db and any async cleanup if needed.
    """
    logger.info("LIFESPAN: starting up - database init")
    #If init_db raises, server will not start
    await init_db()
    
    try:
        yield
    finally:
        logger.info("LIFESPAN: shutting down")

app = FastAPI(
    title="ChronosCore (v0.01)",
    version="0.0.1",
    description="Minimal Chronos API Backend",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




app.include_router(stocks_router)
app.include_router(templates_router)
app.include_router(candidates_router)

@app.get("/", response_class=JSONResponse)
async def root() -> dict:
    """Basic root endpoint."""
    return {"service": "chronos-core-oss", "status": "ok"}


@app.get("/healthz", response_class=JSONResponse)
async def healthz() -> dict:
    """Simple health check for readiness probes."""
    return {"status": "healthy"}
