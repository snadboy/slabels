import logging

logger = logging.getLogger(__name__)

from typing import Optional

from fastapi import APIRouter, HTTPException

from services.sync import sonarr_to_plex

router = APIRouter()

@router.post("/sync_labels/")
async def sync_labels(title: Optional[str] = ""):
    """
    Sync labels from Sonarr to Plex
    for a given title.  If no title is provided, all titles will be processed.

    Args:
        title: The title to search for. Note, if no title is provided, all titles will be processed.
                    Also, title searches are case insensitive AND will accept partial matches.

    Returns:
        {
            "status": {
                "error": boolean, 
                "message": str
            },
            "search": {
                "days": int, 
                "title": str
            }, 
            "changes": [
                {
                    str: {                      # Title of show
                        "added": [str],         # Labels added  
                        "removed": [str]        # Labels removed
                    }
                }
            ]
        }

    Raises:
        HTTPException: If an exception occurs during the process.
    """
    try:
        logger.info(f"sync_labels: {title}")
        return await sonarr_to_plex(title=title)
    except Exception as e:
        HTTPException(status_code=500, detail=f"Exception: {e}")

