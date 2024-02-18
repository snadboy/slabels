import logging
import logging.config

from log_secret import SecretFilter

logging.config.fileConfig("log_config.ini", disable_existing_loggers=False)
logging.getLogger().addFilter(SecretFilter())
logger = logging.getLogger(__name__)

import asyncio
import concurrent.futures
from contextlib import asynccontextmanager
from time import perf_counter
from typing import Any, Callable, Optional

from fastapi import FastAPI
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

        # Startup tasks
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=Config.MAX_THREADS)
        loop = asyncio.get_running_loop()
        loop.set_default_executor(executor)

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
                results = await asyncio.to_thread(lambda: sonarr_to_plex())
            except Exception as e:
                logger.exception(f"Autosync EXCEPTION: {e}")
                raise
            await asyncio.sleep(Config.SYNC_INTERVAL_SECS)
    except asyncio.CancelledError:
        logger.info("Autosync cancelled")
        raise


app = FastAPI(lifespan=app_lifespan)


@app.post("/sonarr_event/")
async def sonarr_event(data: dict):
    if data.get("eventType") in [
        member.value for member in SonarrEventType.__members__.values()
    ]:
        title = data.get("series", {}).get("title")
        results = await asyncio.to_thread(lambda: sonarr_to_plex(title=title))
        logger.info(f"sonarr_event results: {results}")
        # asyncio.create_task(in_thread(lambda: Shows(Config.PLEX_URL, Config.PLEX_TOKEN, Config.SONARR_URL, Config.SONARR_API_KEY).sonarr_to_plex_batch(title=title), f'sonarr_event: {data.get('eventType')}'))
    return JSONResponse(content={"message": "processed successfully"})


@app.post("/fix_labels/")
async def fix_labels(title: Optional[str] = ""):
    logger.info(f"fix_labels: {title}")
    return await asyncio.to_thread(lambda: sonarr_to_plex(title=title), "fix_labels")
    # return await in_thread(lambda: Shows(Config.PLEX_URL, Config.PLEX_TOKEN, Config.SONARR_URL, Config.SONARR_API_KEY).sonarr_to_plex_batch(title=title), 'fix_labels')


@app.get("/plex_series/")
async def plex_series(title: Optional[str] = None, days: Optional[int] = None):
    logger.info(f"plex_series: title: {title} - days: {days}")
    return await asyncio.to_thread(
        lambda: SonarrFuncs().plex_series_search(title=title, days=days), "plex_series"
    )
    # return await in_thread(lambda: Shows(Config.PLEX_URL, Config.PLEX_TOKEN, Config.SONARR_URL, Config.SONARR_API_KEY).plex_series_search(title=title, days=days), 'plex_series')


# if __name__ == "__main__":
#     import logging.config

#     logging.config.fileConfig("log_config.ini", disable_existing_loggers=False)

#     import uvicorn

#     uvicorn.run("app:app", host="0.0.0.0", port=8000, log_level=logging.INFO, reload=True),
