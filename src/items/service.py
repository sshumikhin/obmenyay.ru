from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from src.items.models import Item, UserSeenItem
from src.trades.models import ItemTrade


async def create_item(
    vk_user_id: int,
    session: AsyncSession,
    name: str,
    description: Optional[str],
    s3_path: str,
    is_available: bool = True,
) -> Item:

    new_item = Item(
        name=name,
        description=description,
        owner_id=vk_user_id,
        s3_url_path=s3_path,
        is_available=is_available
    )
    session.add(new_item)
    await session.flush()
    return new_item


async def skip_item(
    session: AsyncSession,
    item_id: int,
    vk_user_id: int
):
    try:
        session.add(
            UserSeenItem(
                user_id = vk_user_id,
                item_id = item_id
        ))
        await session.commit()
    except IntegrityError as e:
        await session.rollback()


async def like_item(
        session: AsyncSession,
        item_id: int,
        vk_user_id: int
):
    try:
        session.add(
            ItemTrade(
                offered_by_user_id = vk_user_id,
                item_requested_id = item_id
            )
        )
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
