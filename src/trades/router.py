from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from vk_id import User as VKUser
from src.items.models import Item
from src.postgres.api import get_entity_by_params
from src.vk.dependencies import get_current_user
from src.postgres.session import async_session
from .models import ItemTrade
from .schemas import DesiredItem, Message
from sqlalchemy import and_, or_

from .services import create_message

trades = APIRouter(
    prefix="/trades",
    tags=["Trades API"]
)


@trades.post("/{trade_id}/choose-item")
async def accept_trade_endpoint(
        desired_item: DesiredItem,
        trade_id: int,
        vk_user: VKUser = Depends(get_current_user),
        session: AsyncSession = Depends(async_session)
):

    user_items_ids = await get_entity_by_params(
        session=session,
        model=Item.id,
        conditions=[
            Item.owner_id == int(vk_user.user_id)
        ],
        many=True
    )

    trade = await get_entity_by_params(
        session=session,
        model=ItemTrade,
        conditions=[
                ItemTrade.item_requested_id.in_(user_items_ids),
                ItemTrade.id == trade_id
        ],
        load_relationships=[
            ItemTrade.item_requested,
            ItemTrade.interested_by_owner_item,
            ItemTrade.interested_user
        ],
    )

    if trade is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Трейд не был найден"}
        )

    desired_item = await get_entity_by_params(
        model=Item,
        session=session,
        conditions=[
            Item.id == desired_item.item_id
        ]
    )

    if desired_item is None or int(desired_item.owner_id) != int(trade.offered_by_user_id):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "У пользователя отсутствует данный предмет"}
        )

    existing_trade = await get_entity_by_params(
        model=ItemTrade,
        session=session,
        conditions=[
            or_(
                and_(ItemTrade.item_requested_id == desired_item.id,
                     ItemTrade.interested_item_id == trade.item_requested_id),
                and_(ItemTrade.item_requested_id == trade.item_requested_id,
                     ItemTrade.interested_item_id == desired_item.id),
            )
        ])

    if existing_trade is not None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "У вас уже есть активный трейд с данными предметами"}
        )

    trade.interested_item_id = desired_item.id
    await session.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "OK"}
    )


@trades.post("/{trade_id}/match")
async def match_trade_endpoint(
        trade_id: int,
        vk_user: VKUser = Depends(get_current_user),
        session: AsyncSession = Depends(async_session)
):
    trade = await get_entity_by_params(
        session=session,
        model=ItemTrade,
        conditions=[
            ItemTrade.id == trade_id,
            ItemTrade.offered_by_user_id == int(vk_user.user_id),
            ItemTrade.interested_item_id.isnot(None)
        ]
    )

    if trade is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Трейд не был найден"}
        )

    trade.is_matched = True
    await session.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "OK"}
    )


@trades.delete("/{trade_id}")
async def delete_trade_endpoint(
        trade_id: int,
        vk_user: VKUser = Depends(get_current_user),
        session: AsyncSession = Depends(async_session)
):
    trade = await get_entity_by_params(
        session=session,
        model=ItemTrade,
        conditions=[
            ItemTrade.id == trade_id,
        ],
        load_relationships=[ItemTrade.item_requested]
    )

    if trade is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Трейд не был найден"}
        )

    if trade.offered_by_user_id == int(vk_user.user_id) or trade.item_requested.owner_id == int(vk_user.user_id):
        await session.delete(trade)
        await session.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "OK"}
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Трейд не был найден"}
        )


@trades.post("/{trade_id}/send_message")
async def send_message_endpoint(
        trade_id: int,
        text: Message,
        vk_user: VKUser = Depends(get_current_user),
        session: AsyncSession = Depends(async_session)
    ):

    trade = await get_entity_by_params(
        session=session,
        model=ItemTrade,
        conditions=[
            ItemTrade.id == trade_id
        ],
        load_relationships=[ItemTrade.item_requested]
    )

    # if trade is None or trade.offered_by_user_id != int(vk_user.user_id) or trade.item_requested.owner_id != int(vk_user.user_id):
    #     return JSONResponse(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         content={"message": "Трейд не был найден"}
    #     )

    await create_message(
        session=session,
        trade_id=trade_id,
        user_id=int(vk_user.user_id),
        text=text.text)

    return {"message": "ok"}
