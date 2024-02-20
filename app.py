import logging
import logging.config
from importlib import import_module

from log_secret import SecretFilter

logging.config.fileConfig("log_config.ini", disable_existing_loggers=False)
logging.getLogger().addFilter(SecretFilter())
logger = logging.getLogger(__name__)

import asyncio

# import concurrent.futures
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI

from config import Config
from sync_funcs import sonarr_to_plex


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    task_autosync = None

    try:
        # Log values of Config constants
        Config.log_constants()

        # Create task to execute every Config.SYNC_INTERVAL_MINS minutes
        task_autosync = asyncio.create_task(autosync())

        # Wait for shutdown
        yield
    finally:
        if task_autosync is not None:
            task_autosync.cancel()
            await task_autosync
app = FastAPI(lifespan=app_lifespan)

async def autosync():
    # TODO: add comments
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

router_files = Path('routers').rglob('*.py')
for router_file in router_files:
    router_module = import_module(f'routers.{router_file.stem}')
    app.include_router(router_module.router)
    
if __name__ == "__main__":
    import logging.config

    logging.config.fileConfig("log_config.ini", disable_existing_loggers=False)

    import uvicorn

    # TODO uvicorn needs to use log_config.ini for logging
    uvicorn.run(
        "app:app", host="0.0.0.0", port=8001, log_level=logging.INFO, reload=False
    ),
