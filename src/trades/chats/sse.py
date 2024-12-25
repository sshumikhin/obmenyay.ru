import asyncio
import json
import vk_id
from sqlalchemy.exc import SQLAlchemyError

from .router import router
from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse
from src.items.models import Item
from src.postgres.api import get_entity_by_params
from src.postgres.session import async_session
from src.vk.constants import JWTTokens
from ..services import get_active_trades
active_sse_connections = set()


@router.get("/sse")
async def chats_sse(request: Request):
    async def stream():
        user = None

        try:
            user = await vk_id.get_user_public_info(
                access_token=request.cookies.get(str(JWTTokens.ACCESS.value)),
            )

        except Exception as e:
            print(f"Error getting user info: {e}") # Логируем ошибку
            active_sse_connections.discard(request) # Безопасное удаление

        finally:
            if isinstance(user, vk_id.Error) or user is None:
                active_sse_connections.discard(request)

        if user is None: # Важная проверка, чтобы избежать ошибок ниже
            yield f"{json.dumps({'type': 'error', 'message': 'User not authenticated'})}\n\n"
            return


        try:
            while True:
                async with async_session() as session:
                    try:
                        user_items = await get_entity_by_params(
                            session=session,
                            model=Item.id,
                            conditions=[Item.owner_id == int(user.user_id)],
                            many=True
                        )

                        chats_list = await get_active_trades(
                           session=session,
                           user_items_ids=user_items,
                           current_user_id=int(user.user_id)
                        )

                        yield f"{json.dumps({'type': 'actual_chats', 'chats': chats_list})}\n\n"
                        await asyncio.sleep(5)

                    except SQLAlchemyError as e:
                        print(f"Database error: {e}")
                        await session.rollback()
                        yield f"{json.dumps({'type': 'error', 'message': 'Database error'})}\n\n" # Отправляем сообщение об ошибке клиенту
                        break
                    except Exception as e:
                        print(f"Other error during DB operation: {e}")
                        yield f"{json.dumps({'type': 'error', 'message': 'Internal server error'})}\n\n"
                        break

        except asyncio.CancelledError:
            print("Client disconnected from SSE")
        except Exception as e:
            print(f"Unexpected error in SSE stream: {e}")

    return EventSourceResponse(stream(), media_type="text/event-stream")