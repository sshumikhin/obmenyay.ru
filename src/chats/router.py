import asyncio
import json
from typing import List, Dict, Optional

import vk_id
from fastapi import APIRouter, Request, Depends
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from src.chats.services import get_active_trades
from src.items.models import Item
from src.jinja import templates
from src.postgres.api import get_entity_by_params
from src.postgres.session import async_session
from src.vk.constants import JWTTokens
from src.vk.dependencies import get_current_user

router = APIRouter(
    prefix="/chats"
)


chats_data: Dict[int, dict] = {
    1: {
        "trade_id": 1,
        "is_my_item": True,
        "user": {"fullname": "Иван", "image_url": "/path/to/avatar1.jpg"},
        "item": {"id": 10, "name": "Велосипед"},
        "last_message": "Привет!"
    },
    2: {
        "trade_id": 2,
        "is_my_item": False,
        "user": {"fullname": "Петр", "image_url": "/path/to/avatar2.jpg"},
        "item": {"id": 11, "name": "Книга"},
        "last_message": "Как дела?"
    },
    3: {
        "trade_id": 3,
        "is_my_item": True,
        "user": {"fullname": "Анна", "image_url": "/path/to/avatar3.jpg"},
        "item": {"id": 12, "name": "Телефон"},
        "last_message": None
    },
}

active_connections: List[WebSocket] = []


async def send_chats_update(websocket: WebSocket):
    chats_list = list(chats_data.values())
    await websocket.send_text(json.dumps({"type": "chats_update", "chats": chats_list}))


async def send_initial_chats(websocket: WebSocket, session, user_id: int):

    user_items = await get_entity_by_params(
        session=session,
        model=Item.id,
        conditions=[
            Item.owner_id == user_id
        ],
        many=True
    )

    chats_list = await get_active_trades(
        session=session,
        user_items_ids=user_items,
        current_user_id=user_id
    )


    chats = {}

    idx = 1
    for chat in chats_list:
        chats[idx] = chat
        idx += 1

    chats = list(chats.values())
    await websocket.send_text(json.dumps({"type": "initial_chats", "chats": chats}))


@router.get("/")
async def get_chats(request: Request, trade_id: Optional[int] = None):
    if trade_id is None:
        return templates.TemplateResponse("chats.html", {"request": request})

    return templates.TemplateResponse("messages.html", {"request": request})


active_sse_connections = set()


async def get_chats_for_user(session: AsyncSession, user_id: int):
    # result = await session.execute(select(Chat).where(Chat.user_id == user_id))
    # chats = result.scalars().all()
    # return chats
    return [
        {"trade_id": 1, "is_my_item": True, "user": {"image_url":"url", "fullname": "name"}, "item": {"id": 1, "name": "item"}, "last_message": {"is_seen": True, "text": "text"}},
        {"trade_id": 2, "is_my_item": False, "user": {"image_url":"url", "fullname": "name2"}, "item": {"id": 2, "name": "item2"}, "last_message": {"is_seen": False, "text": "text2"}}
    ]


@router.get("/sse")
async def chats_sse(request: Request, session: AsyncSession = Depends(async_session)):
    async def stream():
        user = await vk_id.get_user_public_info(
            access_token=request.cookies.get(str(JWTTokens.ACCESS.value)),
        )
        if isinstance(user, vk_id.Error) or user is None:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Unauthorized'})}\n\n"
            return
        active_sse_connections.add(request)
        try:
            while True:
                chats = await get_chats_for_user(session, int(user.user_id))
                data = {"type": "initial_chats", "chats": chats}
                yield f"data: {json.dumps(data)}\n\n"
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            print("Client disconnected from SSE")
        finally:
            active_sse_connections.remove(request)

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.get(
    path="/1")
async def test_endpoint(
        vk_user: vk_id.User = Depends(get_current_user),
        session: AsyncSession = Depends(async_session)):
    user_items = await get_entity_by_params(
        session=session,
        model=Item.id,
        conditions=[
            Item.owner_id == int(vk_user.user_id)
        ],
        many=True
    )

    chats_list = await get_active_trades(
        session=session,
        user_items_ids=user_items,
        current_user_id=int(vk_user.user_id)
    )

    return chats_list

