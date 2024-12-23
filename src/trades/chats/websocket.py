import asyncio
import json

import vk_id
from fastapi import WebSocket, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocketDisconnect
from .router import router
from ..models import ItemTrade
from ...items.models import Item
from ...postgres.api import get_entity_by_params
from ...postgres.session import async_session
from ...vk.constants import JWTTokens
from sqlalchemy import or_, and_
from src.s3_client import PUBLIC_URL as S3_PUBLIC_URL
from .websocket_service import ChatConnection


@router.websocket("/ws/{trade_id}")
async def websocket_endpoint(websocket: WebSocket,
                             trade_id: int,
                             session: AsyncSession = Depends(async_session)):

    # TODO: проверка на то, является ли сейчас trade активным, потому что его могли удалить

    connection = ChatConnection(
        websocket=websocket,
        session=session,
        trade_id=trade_id
    )
    await connection.get_user()
    await connection.get_user_items()
    await connection.get_trade()

    try:
        while True:
            await connection.send_chat()
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        print("Client disconnected")
    except json.JSONDecodeError:
        print("Invalid JSON received")



# @router.websocket("/ws/{trade_id}")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     await websocket.send_json({"type": "active"})
#
#     while True:
#         await websocket.send_json(
#             {
#                 "type": "message",
#                 "text": "Hi there!",
#                 "is_my": False,
#                 "sender_image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTfDJiiBpVN06bimtLeb87RoNiapoZ5sF7zIg&s"
#             }
#         )
#         await websocket.send_json(
#             {
#                 "type": "message",
#                 "text": "Sup mann",
#                 "is_my": True,
#                 "sender_image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTfDJiiBpVN06bimtLeb87RoNiapoZ5sF7zIg&s"
#             }
#         )
#         await asyncio.sleep(5)
#
