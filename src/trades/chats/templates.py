from typing import List, Dict, Optional
from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.jinja import templates
from .router import router
from ..models import ItemTrade
from ...items.models import Item
from ...postgres.api import get_entity_by_params
from ...postgres.session import async_session
from ...vk.dependencies import get_current_user
from ...vk.models import User


@router.get("/")
async def get_chats(
        request: Request,
        trade_id: Optional[int] = None,
        vk_user = Depends(get_current_user),
        session: AsyncSession = Depends(async_session)
):
    if trade_id is None:
        return templates.TemplateResponse("chats.html", {"request": request})

    trade = await get_entity_by_params(
        model=ItemTrade,
        session=session,
        conditions=[ItemTrade.id == trade_id],
        load_relationships=[ItemTrade.item_requested, ItemTrade.interested_user, ItemTrade.interested_by_owner_item]
    )

    if trade is None:
        return templates.TemplateResponse("base.html", {"request": request})

    if trade.item_requested.owner_id == int(vk_user.user_id):
        fullname = trade.interested_user.fullname
    elif trade.offered_by_user_id != int(vk_user.user_id):
        owner = await get_entity_by_params(
            model=User,
            session=session,
            conditions=[User.id == trade.item_requested.owner_id]
        )
        fullname = owner.fullname
    else:
        return templates.TemplateResponse("base.html", {"request": request})

    first_item = trade.interested_by_owner_item

    if first_item is None:
        first_item_name = "Выберите вещь"
    else:
        first_item_name = first_item.name

    return templates.TemplateResponse("messages.html",
                                      {"request": request,
                                       "trade_id": trade_id,
                                       "fullname": fullname,
                                       "first_item_name": first_item_name,
                                       "second_item_name": trade.item_requested.name})
