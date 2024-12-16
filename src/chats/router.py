from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_
from src.items.models import Item, ItemTrade
from src.jinja import templates
from vk_id import User as VKUser

from src.postgres.api import get_entity_by_params
from src.postgres.session import async_session
from src.vk.dependencies import get_current_user

router = APIRouter(
    prefix="/chats"
)


@router.get("/")
async def get_my_active_chats_endpoint(
        request: Request,
        # current_user: VKUser = Depends(get_current_user),
        # session: AsyncSession = Depends(async_session),

):

    # user_items_ids = await get_entity_by_params(
    #     session=session,
    #     model=Item.id,
    #     conditions=[
    #         Item.owner_id == current_user.id,
    #         Item.is_available],
    #     many=True
    # )

    items = [
        {
            "trade_id": 123432,
            "user": {
                "fullname": 'Тестовый чат',
                "image_url": "https://avatars.mds.yandex.net/i?id=561543dbc4c04e48e3dfecb21134d955_l-4299853-images-thumbs&n=13"
            },
            "item": {
                "id": 12323,
                "name": 'Карандаш2'
            },
            "last_message": "Нет, не согласен",
            "is_my_item": True
        },
        {
            "trade_id": 133432,
            "user": {
                "fullname": 'Александр',
                "image_url": "https://avatars.mds.yandex.net/i?id=561543dbc4c04e48e3dfecb21134d955_l-4299853-images-thumbs&n=13"
            },
            "item": {
                "id": 12343,
                "name": 'тетрадь'
            },
            "last_message": "Да, давай. Согласен встретиться на перемене",
            "is_my_item": False
        }
    ];

    return templates.TemplateResponse(
        "messages.html",
        {"request": request,
         "my_items": items}
    )
