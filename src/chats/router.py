import asyncio
import json
from typing import List, Dict

import vk_id
from fastapi import APIRouter, Request, Depends
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from src.chats.services import get_active_trades
from src.items.models import Item
from src.jinja import templates
from src.postgres.api import get_entity_by_params
from src.postgres.session import async_session
from src.vk.constants import JWTTokens

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

    await websocket.send_text(json.dumps({"type": "initial_chats", "chats": chats_list}))


@router.get("/")
async def get_chats(request: Request):
    return templates.TemplateResponse("messages.html", {"request": request})


@router.websocket("/ws/")
async def websocket_endpoint(
        websocket: WebSocket,
        session: AsyncSession = Depends(async_session)
):

    await websocket.accept()

    user = None

    try:
        user = await vk_id.get_user_public_info(
            access_token=websocket.cookies.get(str(JWTTokens.ACCESS.value))
        )
    except Exception as _:
        await websocket.close()

    finally:
        if isinstance(user, vk_id.Error) or user is None:
            await websocket.close()

    active_connections.append(websocket)

    try:
        await send_initial_chats(
            websocket=websocket,
            session=session,
            user_id=int(user.user_id)
        )

        while True:
            data = await websocket.receive_json()
            if data.get("type") == "get_chats":
                await send_initial_chats(websocket)
            elif data.get("type") == "send_message":
                chat_id = data.get("chat_id")
                message = data.get("message")
                if chat_id and message:
                    chats_data[chat_id]["last_message"] = message
                    for connection in active_connections:
                        await connection.send_text(json.dumps({
                            "type": "new_message",
                            "chat_id": chat_id,
                            "message": message
                        }))
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print("Client disconnected")
    except RuntimeError as e:
        print(f"RuntimeError: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")