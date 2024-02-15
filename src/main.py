from enum import Enum
from typing import Optional, Callable, Any
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from time import perf_counter
import asyncio
from contextlib import asynccontextmanager
import concurrent.futures
from src.sblog import logger, logging
from src.shows import Shows

class Config:
    PLEX_URL = None
    PLEX_TOKEN = None

    SONARR_URL = None
    SONARR_API_KEY = None

    MAX_WORKERS = 5
    SYNC_INTERVAL_SECS = 60

    @staticmethod
    def initialize():
        import os
        Config.PLEX_URL = os.getenv('PLEX_URL')
        Config.PLEX_TOKEN = os.getenv('PLEX_TOKEN')
        Config.SONARR_URL = os.getenv('SONARR_URL')
        Config.SONARR_API_KEY = os.getenv('SONARR_API_KEY')

    @staticmethod
    def log_constants():
        redact = ['PLEX_TOKEN', 'SONARR_API_KEY']
        constants = {attr: getattr(Config, attr) for attr in dir(Config) if not callable(getattr(Config, attr)) and not attr.startswith("__")}
        for key, value in constants.items():
            logging.info(f"{key}: {"*****" if key in redact else value}")

Config.initialize()
Config.log_constants()

queue = asyncio.Queue()
showsT = Shows(Config.PLEX_URL, Config.PLEX_TOKEN, Config.SONARR_URL, Config.SONARR_API_KEY)
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=Config.MAX_WORKERS)

# class WorkType(Enum):
#     SONARR_EVENT = "sonarr_event"
#     AUTOSYNC = "autosync"
class SonarrEventType(Enum):
    DOWNLOAD = "Download"
    TEST = "Test"

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # Startup code here
    task = asyncio.create_task(autosync(queue))

    try:
        yield
    finally:
        # Shutdown code here
        task.cancel()
        await task
async def autosync(queue):
    while True:
        await in_thread(lambda: Shows(Config.PLEX_URL, Config.PLEX_TOKEN, Config.SONARR_URL, Config.SONARR_API_KEY).sonarr_to_plex_batch(), 'autosync')
        await asyncio.sleep(Config.SYNC_INTERVAL_SECS)
async def in_thread(thread_func: Callable, name: str) -> Optional[Any]:
    if thread_func is None:
        raise ValueError("thread_func cannot be None")
    
    def thread_func_debug():
        a = perf_counter()
        logger.info(f"worker thread [{name}] starting")
        result = thread_func()
        logger.info(f"Worker thread [{name}] finished - {perf_counter()-a} seconds")
        logger.info(f"Worker thread [{name}] result: {result}")
        return result

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(thread_pool, thread_func_debug)
    return 

app = FastAPI(lifespan=app_lifespan)

@app.post("/sonarr_event/")
async def sonarr_event(data: dict):
    if (data.get('eventType') in [member.value for member in SonarrEventType.__members__.values()]):
        title = data.get('series', {}).get('title')
        asyncio.create_task(in_thread(lambda: Shows(Config.PLEX_URL, Config.PLEX_TOKEN, Config.SONARR_URL, Config.SONARR_API_KEY).sonarr_to_plex_batch(title=title), f'sonarr_event: {data.get('eventType')}'))
    return JSONResponse(content={"message": "processed successfully"})

@app.post("/fix_labels/")
async def fix_labels(title: Optional[str] = ''):
    return await in_thread(lambda: Shows(Config.PLEX_URL, Config.PLEX_TOKEN, Config.SONARR_URL, Config.SONARR_API_KEY).sonarr_to_plex_batch(title=title), 'fix_labels')

@app.get("/plex_series/")
async def plex_series(title: Optional[str] = None, days: Optional[int] = None):
    return await in_thread(lambda: Shows(Config.PLEX_URL, Config.PLEX_TOKEN, Config.SONARR_URL, Config.SONARR_API_KEY).plex_series_search(title=title, days=days), 'plex_series')

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000, log_level=logging.INFO)
