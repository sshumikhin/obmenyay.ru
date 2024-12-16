from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, case
from sqlalchemy.orm import selectinload

from src.items.models import ItemTrade
from src.postgres.api import get_entity_by_params


async def get_active_trades(
        session: AsyncSession,
        user_items_ids: list,
        current_user_id: int
):
    # query = select(ItemTrade).where(
    #     or_(
    #         ItemTrade.item_requested_id.in_(user_items_ids),
    #         ItemTrade.offered_by_user_id == current_user_id
    #     )
    # ).with_only_columns([
    #     ItemTrade,
    #     case((ItemTrade.item_requested_id.in_(user_items_ids), True), else_=False).label("is_my_item")
    # ]).options(
    #     selectinload(ItemTrade.item_requested)
    # )
    #
    # trades = (await session.execute(query)).scalars().all()
    #
    # for trade in trades:
    #     trade.last_message = await get_entity_by_params(
    #         session=session,
    #         model=Message
    #     )
    #
    # return
    pass

    # trades = await get_entity_by_params(
    #     session=session,
    #     model=ItemTrade,
    #     conditions=[
    #         or_(ItemTrade.item_requested_id.in_(user_items_ids), ItemTrade.offered_by_user_id == current_user.id)
    #     ],
    #     many=True,
    #     load_relationships=[ItemTrade.item_requested]
    # )