from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, case
from sqlalchemy.orm import selectinload

from src.chats.models import Message
from src.items.models import ItemTrade, Item
from src.postgres.api import get_entity_by_params


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
    ).with_only_columns([
        ItemTrade,
        case((ItemTrade.item_requested_id.in_(user_items_ids), True), else_=False).label("is_my_item")
    ]).options(
        selectinload(ItemTrade.item_requested),
        selectinload(ItemTrade.interested_user),
        selectinload(Item.owner)
    )

    trades = (await session.execute(query)).scalars().all()

    content = []
    for trade in trades:
        trade_info = {}
        trade_info["trade_id"] = trade.id
        trade_info["is_my_item"] = trade.is_my_item

        if trade.is_my_item:
            trade_info["user"] = {
                "fullname": trade.interested_user.fullname,
                "image_url": trade.interested_user.image_url
            }
        else:
            trade_info["user"] = {
                "fullname" : trade.owner.fullname,
                "image_url": trade.owner.image_url
            }

        trade_info["item"] = {
            "id": trade.item_requested.id,
            "name": trade.item_requested.name
        }

        trade_info["last_message"] = {
            "text": "Текст последнего сообщения",
            "is_seen": False
        }

        content.append(trade)

    # for trade in trades:
    #     trade.last_message = await get_entity_by_params(
    #         session=session,
    #         model=Message,
    #         conditions=[
    #             Message.trade_id == trade.id,
    #         ]
    #     )

    return content

    # trades = await get_entity_by_params(
    #     session=session,
    #     model=ItemTrade,
    #     conditions=[
    #         or_(ItemTrade.item_requested_id.in_(user_items_ids), ItemTrade.offered_by_user_id == current_user.id)
    #     ],
    #     many=True,
    #     load_relationships=[ItemTrade.item_requested]
    # )