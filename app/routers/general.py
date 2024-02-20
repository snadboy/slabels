import logging

logger = logging.getLogger(__name__)

from typing import Optional

from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Heartbeat"}