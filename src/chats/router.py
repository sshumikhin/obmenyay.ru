import asyncio
import json
from typing import List, Dict

from fastapi import APIRouter, Request, Depends
from fastapi import WebSocket, WebSocketDisconnect

from src.items.models import Item, ItemTrade
from src.jinja import templates
from vk_id import User as VKUser

from src.postgres.api import get_entity_by_params
from src.postgres.session import async_session
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

async def send_initial_chats(websocket: WebSocket):
    chats_list = list(chats_data.values())
    await websocket.send_text(json.dumps({"type": "initial_chats", "chats": chats_list}))


@router.get("/")
async def get_chats(request: Request):
    return templates.TemplateResponse("messages.html", {"request": request})


@router.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)

    try:
        await send_initial_chats(websocket) # Отправляем начальные данные при подключении

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
            await asyncio.sleep(1) # Чтобы не загружать процессор в цикле
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print("Client disconnected")
    except RuntimeError as e:
        print(f"RuntimeError: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
