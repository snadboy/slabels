import logging
import logging.config

from log_secret import SecretFilter
from plex_funcs import PlexFuncs

logging.config.fileConfig("log_config.ini", disable_existing_loggers=False)
logging.getLogger().addFilter(SecretFilter())
logger = logging.getLogger(__name__)

import asyncio
import concurrent.futures
from contextlib import asynccontextmanager
from time import perf_counter
from typing import Any, Callable, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from config import Config
from enums import SonarrEventType
from sonarr_funcs import SonarrFuncs
from sync_funcs import sonarr_to_plex


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    task_autosync = None

    try:
        Config.log_constants()

        task_autosync = asyncio.create_task(autosync())

        # Wait for shutdown
        yield
    finally:
        if task_autosync is not None:
            task_autosync.cancel()
            await task_autosync


async def autosync():
    try:
        while True:
            try:
                logger.info("Autosync started")
                results = await asyncio.create_task(sonarr_to_plex())
            except Exception as e:
                logger.exception(f"Autosync EXCEPTION: {e}")
                raise
            await asyncio.sleep(Config.SYNC_INTERVAL_MINS * 60)
    except asyncio.CancelledError:
        logger.info("Autosync cancelled")
        raise


app = FastAPI(lifespan=app_lifespan)

@app.get("/")
async def root():
    return {"message": "Heartbeat"}

@app.post("/sonarr_event/")
async def sonarr_event(data: dict):
    if data.get("eventType", "") not in [member.value for member in SonarrEventType.__members__.values()]:
        raise HTTPException(status_code=400, 
            detail=f"Invalid eventType: {data.get('eventType')} - must be one of: {', '.join([member.value for member in SonarrEventType.__members__.values()])}")

    try:
        title = data.get("series", {}).get("title")
        results = await asyncio.to_thread(lambda: sonarr_to_plex(title=title))
        logger.info(f"sonarr_event results: {results}")
        return JSONResponse(content={"message": "processed successfully"})
    except Exception as e:
        HTTPException(status_code=500, detail=f"Exception: {e}")


@app.post("/fix_labels/")
async def fix_labels(title: Optional[str] = ""):
    try:
        logger.info(f"fix_labels: {title}")
        return await asyncio.to_thread(lambda: sonarr_to_plex(title=title), "fix_labels")
    except Exception as e:
        HTTPException(status_code=500, detail=f"Exception: {e}")


@app.get("/plex_series/")
async def plex_series(title: Optional[str] = None, days: Optional[int] = None):
    if days and days < 0:
        raise HTTPException(status_code=400, 
            detail=f"Invalid value for days: {days} - if present, it must be zero or a positive integer")

    try:
        logger.info(f"plex_series: title: {title} - days: {days}")
        return await asyncio.to_thread(lambda: PlexFuncs().plex_series_search(title=title, days=days))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Exception: {e}")

if __name__ == "__main__":
    import logging.config

    logging.config.fileConfig("log_config.ini", disable_existing_loggers=False)

    import uvicorn

    uvicorn.run(
        "app:app", host="0.0.0.0", port=8001, log_level=logging.INFO, reload=True
    ),
