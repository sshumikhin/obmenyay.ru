from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.items.models import Item, ItemStatus


async def create_item(
    vk_user_id: int,
    session: AsyncSession,
    name: str,
    description: Optional[str],
    s3_path: str,
    status: ItemStatus
) -> Item:

    new_item = Item(
        name=name,
        description=description,
        owner_id=vk_user_id,
        s3_url_path=s3_path,
        status_id = status.id
    )
    session.add(new_item)
    await session.flush()
    return new_item
