import asyncio
import json
from typing import List, Dict, Optional

import vk_id
from fastapi import APIRouter, Request, Depends
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse
from starlette.websockets import WebSocketDisconnect

from src.chats.services import get_active_trades
from src.items.models import Item
from src.jinja import templates
from .router import router
from src.postgres.api import get_entity_by_params
from src.postgres.session import async_session
from src.vk.constants import JWTTokens


@router.get("/")
async def get_chats(request: Request, trade_id: Optional[int] = None):
    if trade_id is None:
        return templates.TemplateResponse("chats.html", {"request": request})

    return templates.TemplateResponse("messages.html", {"request": request})
