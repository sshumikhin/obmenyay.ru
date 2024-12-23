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



status_db = "waiting for owner"


@router.websocket("/ws/{trade_id}")
async def websocket_endpoint(websocket: WebSocket,
                             trade_id: int,
                             session: AsyncSession = Depends(async_session)):

    # TODO: проверка на то, является ли сейчас trade активным, потому что его могли удалить


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
            return

    async def get_user_items(session: AsyncSession):
        user_items_ids = await get_entity_by_params(
            session=session,
            model=Item.id,
            conditions=[
                Item.owner_id == int(user.user_id)
            ],
            many=True
        )

        trade = await get_entity_by_params(
            session=session,
            model=ItemTrade,
            conditions=[
                and_(
                    or_(
                        ItemTrade.item_requested_id.in_(user_items_ids),
                        ItemTrade.offered_by_user_id == int(user.user_id),
                ),
                        ItemTrade.id == trade_id
                )
            ],
            load_relationships=[
                ItemTrade.item_requested,
                ItemTrade.interested_by_owner_item,
                ItemTrade.interested_user
            ],
        )

        if trade is None:
            await websocket.close()
            return

        initial_payload = {"type": "initial_data"}

        if trade.interested_item_id is None and trade.item_requested.owner_id == int(user.user_id):
            initial_payload["status"] = "choose item"

            items = await get_entity_by_params(
                model=Item,
                session=session,
                conditions=[
                    Item.owner_id == trade.offered_by_user_id
                ],
                many=True
            )

            content = []
            for item in items:
                content.append({
                    "id": item.id,
                    "name": item.name,
                    "image": f"{S3_PUBLIC_URL}/{item.s3_url_path}"
                })
            initial_payload["items"] = content

        elif trade.interested_item_id is None and trade.item_requested.owner_id != int(user.user_id):
            initial_payload["status"] = "waiting"
        elif trade.interested_item_id is not None and trade.is_matched is False and trade.item_requested.owner_id == int(user.user_id):
            initial_payload["status"] = "waiting"
        elif trade.interested_item_id is not None and trade.is_matched is False and trade.item_requested.owner_id != int(user.user_id):

            initial_payload["status"] = "final answer"

            second_item = await get_entity_by_params(
                model=Item,
                session=session,
                conditions=[Item.id == trade.interested_item_id]
            )

            initial_payload["items"] = [{
                "id": second_item.id,
                "name": second_item.name,
                "image": f"{S3_PUBLIC_URL}/{second_item.s3_url_path}"
            }]
        else:
            initial_payload["status"] = "active"

        await websocket.send_json(initial_payload)


    try:
        while True:
            await get_user_items(session)
            await asyncio.sleep(5)
            # data = await websocket.receive_json()
            # if data.get("type") == "get_all_data":
            #     await websocket.send_json({
            #         "type": "initial_data",
            #         "status": status_db,
            #         "items": items_db
            #     })
            #
            #     await asyncio.sleep(4)
            #
            #     await websocket.send_json({
            #         "type": "status",
            #         "status": status_db,
            #         "items": items_db
            #     })
            # elif data.get("type") == "update_status":
            #     status_db = data.get("status")
            #     await websocket.send_json({
            #         "type": "status",
            #         "status": status_db
            #     })
            # else:
            #     await websocket.send_json({"type": "error", "message": "Unknown request type"})

    except WebSocketDisconnect:
        print("Client disconnected")
    except json.JSONDecodeError:
        print("Invalid JSON received")




# @router.websocket("/ws/")
# async def websocket_endpoint(
#         websocket: WebSocket,
#         session: AsyncSession = Depends(async_session)
# ):
#
#     await websocket.accept()
#
#     user = None
#
#     try:
#         user = await vk_id.get_user_public_info(
#             access_token=websocket.cookies.get(str(JWTTokens.ACCESS.value))
#         )
#     except Exception as _:
#         await websocket.close()
#
#     finally:
#         if isinstance(user, vk_id.Error) or user is None:
#             await websocket.close()
#
#     active_connections.append(websocket)
#
#     try:
#         await send_initial_chats(websocket, session=session, user_id=int(user.id))
#
#         while True:
#             data = await websocket.receive_json()
#             if data.get("type") == "get_chats":
#                 await send_initial_chats(websocket)
#             elif data.get("type") == "send_message":
#                 chat_id = data.get("chat_id")
#                 message = data.get("message")
#                 if chat_id and message:
#                     chats_data[chat_id]["last_message"] = message
#                     for connection in active_connections:
#                         await connection.send_text(json.dumps({
#                             "type": "new_message",
#                             "chat_id": chat_id,
#                             "message": message
#                         }))
#             await asyncio.sleep(1)
#     except WebSocketDisconnect:
#         active_connections.remove(websocket)
#         print("Client disconnected")
#     except RuntimeError as e:
#         print(f"RuntimeError: {e}")
#     except Exception as e:
#         print(f"Unexpected error: {e}")