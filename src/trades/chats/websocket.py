import asyncio
import json
from typing import List

from fastapi import WebSocket, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette import EventSourceResponse

from .router import router
from .websocket_errors import ChatIsActive, CloseConnectionError
from ...postgres.session import async_session
from ...vk.constants import JWTTokens
from .websocket_service import ChatConnection


#
# websocket_connections: dict[int, List[WebSocket]] = {}
#
#
#
# async def send_update_to_client(websocket: WebSocket, data):
#     try:
#         await websocket.send_json(data)
#     except RuntimeError:
#         # Обработка случая, когда соединение уже закрыто
#         pass
#
#
# async def broadcast_trade_update(trade_id: int, update_data: dict):
#     if trade_id in websocket_connections:
#         for websocket in websocket_connections[trade_id]:
#             await send_update_to_client(websocket, update_data)
#
#
# async def acting_on_active_trade(
#         connection: ChatConnection,
#         websocket: WebSocket
# ):
#     await websocket.send_json({
#         "type": connection.type,
#     })
#
#     current_messages = await connection.get_all_messages()
#
#     for message in current_messages:
#         await websocket.send_json(message)
#
#     while True:
#         await asyncio.sleep(3)
#         new_messages = await connection.get_new_messages()
#         for message in new_messages:
#             await websocket.send_json(message)
#
#
# @router.websocket("/ws/{trade_id}")
# async def websocket_endpoint(websocket: WebSocket,
#                              trade_id: int,
#                              session: AsyncSession = Depends(async_session)):
#
#     # TODO: проверка на то, является ли сейчас trade активным, потому что его могли удалить
#
#     await websocket.accept()
#
#     if trade_id not in websocket_connections:
#         websocket_connections[trade_id] = []
#     websocket_connections[trade_id].append(websocket)
#
#     try:
#         connection = ChatConnection(
#             session=session,
#         )
#
#         await connection.init_trade(
#             access_token=websocket.cookies.get(str(JWTTokens.ACCESS.value)),
#             trade_id=trade_id
#         )
#
#         while connection.type != "active":
#             update_data = await connection.check_current_state()
#             await send_update_to_client(websocket, update_data)
#             if update_data.get("status") != connection.type:
#                 await broadcast_trade_update(trade_id, update_data)
#                 if update_data.get("status") == "final answer":
#                     connection.type = "final answer"
#                 if update_data.get("status") == "active":
#                     connection.type = "active"
#             await asyncio.sleep(5)
#         await acting_on_active_trade(connection, websocket)
#     except Exception as e:
#         print(f"WebSocket error: {e}")
#     finally:
#         if trade_id in websocket_connections:
#             websocket_connections[trade_id].remove(websocket)
#             if not websocket_connections[trade_id]:
#                 del websocket_connections[trade_id]
#         await websocket.close()



@router.get("/sse/{trade_id}")
async def personal_chat_sse(
        request: Request,
        session: AsyncSession = Depends(async_session),
        trade_id: int = None):


    async def stream():
            connection = ChatConnection(
                session=session,
            )
            try:
                await connection.init_trade(
                    access_token=request.cookies.get(str(JWTTokens.ACCESS.value)),
                    trade_id=trade_id
                )
            except CloseConnectionError:
                return


            try:
                if connection.type == "active":
                    current_messages = await connection.get_all_messages()

                    for message in current_messages:
                        yield f"{json.dumps({message})}"

                    while True:
                        await asyncio.sleep(3)
                        new_messages = await connection.get_new_messages()
                        for message in new_messages:
                            yield f"{json.dumps({message})}"

                else:
                    while True:
                        try:
                            await connection.init_trade(
                                access_token=request.cookies.get(str(JWTTokens.ACCESS.value)),
                                trade_id=trade_id
                            )

                            data=await connection.check_current_state()
                            yield f"{json.dumps(data)}"

                        except ChatIsActive:
                            current_messages = await connection.get_all_messages()

                            for message in current_messages:
                                yield f"{json.dumps({message})}"

                            while True:
                                await asyncio.sleep(3)
                                new_messages = await connection.get_new_messages()
                                for message in new_messages:
                                    yield f"{json.dumps({message})}"

            except asyncio.CancelledError:
                return

    return EventSourceResponse(stream())


