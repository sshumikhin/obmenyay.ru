import asyncio
import json
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect
from .router import router

items_db = [
    {"id": 1, "name": "Ручка", "image": "../static/img/1.jpg"},
    {"id": 2, "name": "Блокнот", "image": "../static/img/fork.png"},
    {"id": 3, "name": "Книга", "image": "../static/img/pencils.png"},
    {"id": 4, "name": "Кружка", "image": "../static/img/3.jpg"},
    {"id": 5, "name": "Игрушка", "image": "../static/img/book.png"},
]

status_db = "waiting for owner"


@router.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    global status_db
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "get_all_data":
                await websocket.send_json({
                    "type": "initial_data",
                    "status": status_db,
                    "items": items_db
                })

                await asyncio.sleep(4)

                await websocket.send_json({
                    "type": "status",
                    "status": status_db,
                    "items": items_db
                })
            elif data.get("type") == "update_status":
                status_db = data.get("status")
                await websocket.send_json({
                    "type": "status",
                    "status": status_db
                })
            else:
                await websocket.send_json({"type": "error", "message": "Unknown request type"})

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