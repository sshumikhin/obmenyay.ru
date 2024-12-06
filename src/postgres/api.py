from typing import Optional, Any, List

# Third party
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


async def get_entity_by_params(
        model: Any,
        session: AsyncSession,
        conditions: List[Any] = None,
        load_relationships: Optional[List[Any]] = None,
        many = False,
        order_by: Any = None,
        offset: int = None,
        limit: int = None
) -> Any:

    query = select(model)

    if load_relationships is not None:
        for relationship in load_relationships:
            query = query.options(selectinload(relationship))

    if conditions is not None:
        query = query.where(*conditions)

    if order_by is not None:
        query = query.order_by(order_by)

    if offset is not None:
        query = query.offset(offset)

    if limit is not None:
        query = query.limit(limit)

    if many:
        result = (await session.execute(query)).scalars().all()
        return result

    result = (await session.execute(query)).scalar_one_or_none()
    return result


async def update_entity_by_params(
        model: Any,
        session: AsyncSession,
        values: dict,
        conditions: list,
        returning: Optional[list] = None) -> Any:

    stmt = update(model).where(*conditions).values(**values)

    if returning is not None:
        stmt = stmt.returning(model)
        result = (await session.execute(stmt)).scalar_one_or_none()
        return result

    await session.execute(stmt)
    await session.commit()
    return


async def delete_entity(
        session: AsyncSession,
        entity: Any) -> Any:
    await session.delete(entity)
