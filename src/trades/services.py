from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, case
from sqlalchemy.orm import selectinload

from src.items.models import Item
from src.postgres.api import get_entity_by_params
from src.trades.models import ItemTrade


async def get_active_trades(
        session: AsyncSession,
        user_items_ids: list,
        current_user_id: int
):

    query = select(ItemTrade).where(
        or_(
            ItemTrade.item_requested_id.in_(user_items_ids),
            ItemTrade.offered_by_user_id == current_user_id
        )
    ).options(
        selectinload(ItemTrade.item_requested).selectinload(Item.owner),
        selectinload(ItemTrade.interested_user),
    )

    trades = (await session.execute(query)).scalars().all()

    content = []

    for trade in trades:
        trade_info = {}
        trade_info["trade_id"] = trade.id
        is_my_item = trade.item_requested.owner_id == current_user_id
        trade_info["is_my_item"] = is_my_item

        if trade.item_requested.owner_id == current_user_id:
            trade_info["user"] = {
                "fullname": trade.interested_user.fullname,
                "image_url": trade.interested_user.image_url
            }
        else:
            trade_info["user"] = {
                "fullname": trade.item_requested.owner.fullname,
                "image_url": trade.item_requested.owner.image_url
            }

        trade_info["item"] = {
            "id": trade.item_requested.id,
            "name": trade.item_requested.name
        }

        trade_info["last_message"] = {
            "text": "Текст последнего сообщения",
        }

        content.append(trade_info)

    return content
