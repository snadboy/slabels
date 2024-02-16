from typing import Optional, Callable, Any
from time import perf_counter
import asyncio
from contextlib import asynccontextmanager
import concurrent.futures
import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from enums import SonarrEventType
from shows import Shows
from sblog import logger
from config import Config

try:
    thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=Config.MAX_THREADS)
except Exception as e:
    logging.error(f"Error creating thread pool: {e}")

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    task_autosync = None

    try:
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
    while True:
        try:
            logger.info("Autosync starting")
            results = await asyncio.to_thread(lambda: Shows(Config.PLEX_URL, Config.PLEX_TOKEN, Config.SONARR_URL, Config.SONARR_API_KEY).sonarr_to_plex_batch())
            logger.info(f"Autosync results: {results}")
        except Exception as e:
            raise
        await asyncio.sleep(Config.SYNC_INTERVAL_SECS)

app = FastAPI(lifespan=app_lifespan)

@app.post("/sonarr_event/")
async def sonarr_event(data: dict):
    if (data.get('eventType') in [member.value for member in SonarrEventType.__members__.values()]):
        title = data.get('series', {}).get('title')
        results = await asyncio.to_thread(lambda: Shows(Config.PLEX_URL, Config.PLEX_TOKEN, Config.SONARR_URL, Config.SONARR_API_KEY).sonarr_to_plex_batch(title=title))
        logger.info(f"sonarr_event results: {results}")
        # asyncio.create_task(in_thread(lambda: Shows(Config.PLEX_URL, Config.PLEX_TOKEN, Config.SONARR_URL, Config.SONARR_API_KEY).sonarr_to_plex_batch(title=title), f'sonarr_event: {data.get('eventType')}'))
    return JSONResponse(content={"message": "processed successfully"})

@app.post("/fix_labels/")
async def fix_labels(title: Optional[str] = ''):
    logger.info(f"fix_labels: {title}")
    return await asyncio.to_thread(lambda: Shows(Config.PLEX_URL, Config.PLEX_TOKEN, Config.SONARR_URL, Config.SONARR_API_KEY).sonarr_to_plex_batch(title=title), 'fix_labels')
    # return await in_thread(lambda: Shows(Config.PLEX_URL, Config.PLEX_TOKEN, Config.SONARR_URL, Config.SONARR_API_KEY).sonarr_to_plex_batch(title=title), 'fix_labels')

@app.get("/plex_series/")
async def plex_series(title: Optional[str] = None, days: Optional[int] = None):
    logger.info(f"plex_series: title: {title} - days: {days}")
    return await asyncio.to_thread(lambda: Shows(Config.PLEX_URL, Config.PLEX_TOKEN, Config.SONARR_URL, Config.SONARR_API_KEY).plex_series_search(title=title, days=days), 'plex_series')
    # return await in_thread(lambda: Shows(Config.PLEX_URL, Config.PLEX_TOKEN, Config.SONARR_URL, Config.SONARR_API_KEY).plex_series_search(title=title, days=days), 'plex_series')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level=logging.INFO)
