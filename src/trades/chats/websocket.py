import asyncio

from fastapi import WebSocket, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .router import router
from .websocket_errors import ChatIsActive
from ...postgres.session import async_session
from ...vk.constants import JWTTokens
from .websocket_service import ChatConnection


async def acting_on_active_trade(
        connection: ChatConnection,
        websocket: WebSocket
):
    await websocket.send_json({
        "type": connection.type,
    })

    current_messages = await connection.get_all_messages()

    for message in current_messages:
        await websocket.send_json(message)

    while True:
        await asyncio.sleep(3)
        new_messages = await connection.get_new_messages()
        for message in new_messages:
            await websocket.send_json(message)


@router.websocket("/ws/{trade_id}")
async def websocket_endpoint(websocket: WebSocket,
                             trade_id: int,
                             session: AsyncSession = Depends(async_session)):

    # TODO: проверка на то, является ли сейчас trade активным, потому что его могли удалить

    await websocket.accept()

    try:
        connection = ChatConnection(
            session=session,
        )

        await connection.init_trade(
            access_token=websocket.cookies.get(str(JWTTokens.ACCESS.value)),
            trade_id=trade_id
        )

        while connection.type != "active":

            try:

                await websocket.send_json(
                    data=await connection.check_current_state()
                )

            except ChatIsActive:
                await acting_on_active_trade(connection, websocket)

            await asyncio.sleep(5)

        await acting_on_active_trade(connection, websocket)

    except Exception as e:
        print(e)
        await websocket.close()
