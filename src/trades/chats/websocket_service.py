from typing import Union

import vk_id
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_
from src.items.models import Item
from src.postgres.api import get_entity_by_params
from src.trades.chats.websocket_errors import CloseConnectionError, ChatIsActive
from src.trades.models import ItemTrade, Message
from src.vk.constants import JWTTokens
from src.s3_client import PUBLIC_URL as S3_PUBLIC_URL


class ChatConnection:

    def __init__(
            self,
    ):
        self.user: None | vk_id.User = None
        self.trade: None | ItemTrade = None
        self.type = None
        self.loaded_messages_ids_in_chat = None

    async def init_trade(
            self,
            access_token: str,
            trade_id: int
    ):
        """Инициализирует трейд и пользователя. А также устанавливает тип трейда"""


        try:
            self.user = await vk_id.get_user_public_info(
                access_token=access_token)
        finally:
            if isinstance(self.user, vk_id.Error) or self.user is None:
                raise CloseConnectionError

        await self.__get_trade(trade_id=trade_id)

    async def __get_trade(
            self,
            session: AsyncSession,
            trade_id: int
    ):
        user_items_ids = await get_entity_by_params(
            session=session,
            model=Item.id,
            conditions=[
                Item.owner_id == int(self.user.user_id)
            ],
            many=True
        )

        self.trade = await get_entity_by_params(
            session=session,
            model=ItemTrade,
            conditions=[
                and_(
                    or_(
                        ItemTrade.item_requested_id.in_(user_items_ids),
                        ItemTrade.offered_by_user_id == int(self.user.user_id),
                    ),
                    ItemTrade.id == trade_id
                )
            ],
            load_relationships=[
                ItemTrade.item_requested,
                ItemTrade.interested_by_owner_item,
                ItemTrade.interested_user
            ],
        )

        if self.trade is None:
            raise CloseConnectionError

        if not self.trade.is_matched:
            self.type = "initial_data"
        else:
            self.type = "active"

    async def _send_companion_items(self, session: AsyncSession):
        items = await get_entity_by_params(
            model=Item,
            session=session,
            conditions=[
                Item.owner_id == self.trade.offered_by_user_id
            ],
            many=True
        )

        content = []
        for item in items:
            content.append({
                "id": item.id,
                "name": item.name,
                "image": f"{S3_PUBLIC_URL}/{item.s3_url_path}"
            })

        return content

    async def _get_item_which_your_companion_wants(self, session: AsyncSession):
            second_item = await get_entity_by_params(
                model=Item,
                session=session,
                conditions=[Item.id == self.trade.interested_item_id]
            )

            content = [{
                "id": second_item.id,
                "name": second_item.name,
                "image": f"{S3_PUBLIC_URL}/{second_item.s3_url_path}"
            }]

            return content

    async def get_all_messages(self, session: AsyncSession):
        messages = await get_entity_by_params(
            session=session,
            model=Message,
            conditions=[
                Message.trade_id == self.trade.id
            ],
            load_relationships=[Message.sender],
            many=True
        )

        self.loaded_messages_ids_in_chat = [message.id for message in messages]

        content = []

        for message in messages:
            content.append({
                "type": "message",
                "text": message.text,
                "sender_image_url": message.sender.image_url,
                "is_my": message.user_id == int(self.user.user_id)
            })
        return content

    async def get_new_messages(self, session: AsyncSession):
        messages = await get_entity_by_params(
            session=session,
            model=Message,
            conditions=[
                Message.trade_id == self.trade.id,
                Message.id.not_in(self.loaded_messages_ids_in_chat)
            ],
            load_relationships=[Message.sender],
            many=True
        )

        content = []

        if messages is not None:

            self.loaded_messages_ids_in_chat.extend([message.id for message in messages])

            for message in messages:
                content.append({
                    "type": "message",
                    "text": message.text,
                    "sender_image_url": message.sender.image_url,
                    "is_my": message.user_id == int(self.user.user_id)
                })

        return content

    async def check_current_state(self, session: AsyncSession):
        """ Только для неактивных чатов """

        current_type = self.type

        await self.__get_trade(trade_id=self.trade.id,session=session)

        if current_type != self.type:
            raise ChatIsActive

        payload = {"type": self.type}

        if self.trade.interested_item_id is None and self.trade.item_requested.owner_id == int(self.user.user_id):
            payload["status"] = "choose item"
            payload["items"] = await self._send_companion_items(session=session)

        elif self.trade.interested_item_id is None and self.trade.item_requested.owner_id != int(self.user.user_id):
            payload["status"] = "waiting"

        elif self.trade.interested_item_id is not None and self.trade.is_matched is False and self.trade.item_requested.owner_id == int(self.user.user_id):
            payload["status"] = "waiting"

        elif self.trade.interested_item_id is not None and self.trade.is_matched is False and self.trade.item_requested.owner_id != int(self.user.user_id):

            payload["status"] = "final answer"
            payload["items"] = await self._get_item_which_your_companion_wants(session=session)

        return payload
