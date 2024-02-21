import logging

logger = logging.getLogger(__name__)

from typing import Optional

from fastapi import APIRouter, HTTPException

from app.services.plex import PlexFuncs

router = APIRouter()

@router.get("/plex_series/")
async def plex_series(title: Optional[str] = None, days: Optional[int] = None):
    # TODO: add comments
    if days and days < 0:
        raise HTTPException(status_code=400, detail=f"Invalid value for days: {days} - if present, it must be zero or a positive integer")

    try:
        logger.info(f"plex_series: title: {title} - days: {days}")
        return await PlexFuncs().plex_series_search(title=title, days=days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Exception: {e}")
