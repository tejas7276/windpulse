import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import config
from .routes import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("windpulse")

app = FastAPI(title="WindPulse API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(router)


@app.exception_handler(Exception)
async def unexpected_error(request, exc):
    # Log the details server-side; the client only gets a generic message.
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
