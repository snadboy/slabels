import logging

logger = logging.getLogger(__name__)

from typing import Optional

from fastapi import APIRouter
import datetime
from fastapi import APIRouter, Request

router = APIRouter()

start_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') 

@router.get("/")
async def root(request: Request):
    server_ip = request.client.host
    server_port = request.client.port    
    return {"message": f"Server up since {start_time} @ {request.base_url}"}  