import logging

logger = logging.getLogger(__name__)

import asyncio

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.helpers.enums import SonarrEventType
from app.services.sonarr import SonarrFuncs
from app.services.sync import sonarr_to_plex

router = APIRouter()

@router.post("/sonarr_event/")
async def sonarr_event(data: dict):
    # TODO: add comments
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

@router.get ("/sonarr_tags/")
async def sonarr_tags():
    # TODO: add comments
    try:
        labels = await asyncio.to_thread(lambda: SonarrFuncs().sonarr_all_tags_by_label())
        keys = labels.keys()
        return list(keys)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Exception: {e}")

