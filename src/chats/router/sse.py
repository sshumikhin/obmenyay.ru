import asyncio
import json
import vk_id
from .router import router
from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse
from src.chats.services import get_active_trades
from src.items.models import Item
from src.postgres.api import get_entity_by_params
from src.postgres.session import async_session
from src.vk.constants import JWTTokens


active_sse_connections = set()


async def get_chats_for_user(session: AsyncSession, user_id: int):
    # result = await session.execute(select(Chat).where(Chat.user_id == user_id))
    # chats = result.scalars().all()
    # return chats
    return [
        {
            "trade_id": 1,
            "is_my_item": True,
            "user":
                {"image_url": "url", "fullname": "name"}, "item": {"id": 1, "name": "item"}, "last_message": {"is_seen": True, "text": "text"}},
        {"trade_id": 2, "is_my_item": False, "user": {"image_url": "url", "fullname": "name2"}, "item": {"id": 2, "name": "item2"}, "last_message": {"is_seen": False, "text": "text2"}}
    ]


@router.get("/sse")
async def chats_sse(request: Request, session: AsyncSession = Depends(async_session)):
    async def stream():
        user = None

        try:
            user = await vk_id.get_user_public_info(
                access_token=request.cookies.get(str(JWTTokens.ACCESS.value)),
            )

        except Exception as _:
            active_sse_connections.remove(request)

        finally:
            if isinstance(user, vk_id.Error) or user is None:
                active_sse_connections.remove(request)
        try:
            while True:
               user_items = await get_entity_by_params(
                    session=session,
                    model=Item.id,
                    conditions=[
                        Item.owner_id == int(user.user_id)
                    ],
                    many=True
               )

               chats_list = await get_active_trades(
                  session=session,
                  user_items_ids=user_items,
                  current_user_id=int(user.user_id)
               )

               yield f"{json.dumps({"type": "actual_chats", "chats": chats_list})}\n\n"

               await asyncio.sleep(5)

        except asyncio.CancelledError:
            print("Client disconnected from SSE")

    return EventSourceResponse(stream())