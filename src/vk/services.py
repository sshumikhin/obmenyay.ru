from sqlalchemy.ext.asyncio import AsyncSession
from .models import User


async def create_user(
        session: AsyncSession,
        user_id: int,
        fullname: str,
        image_url: str
):
    session.add(
        User(
            id=user_id,
            fullname=fullname,
            image_url=image_url
        )
    )

    await session.flush()