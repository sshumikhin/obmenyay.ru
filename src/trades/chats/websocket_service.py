from typing import Union

import vk_id
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_
from src.items.models import Item
from src.postgres.api import get_entity_by_params
from src.trades.models import ItemTrade, Message
from src.vk.constants import JWTTokens
from src.s3_client import PUBLIC_URL as S3_PUBLIC_URL


class ChatConnection:

    def __init__(
            self,
            websocket: WebSocket,
            session: AsyncSession,
            trade_id: int
    ):
        self.websocket = websocket
        self.session = session
        self.user: None | vk_id.User = None
        self.user_items_ids = None
        self.trade_id = trade_id
        self.trade: None | ItemTrade = None
        self.status = None
        self.messages_in_chat = None

    async def get_user(self):

        await self.websocket.accept()

        try:
            self.user = await vk_id.get_user_public_info(
                access_token=self.websocket.cookies.get(str(JWTTokens.ACCESS.value))
            )
        except Exception as _:
            await self.websocket.close()
        finally:
            if isinstance(self.user, vk_id.Error) or self.user is None:
                await self.websocket.close()
                return

    async def get_user_items(self):
        self.user_items_ids = await get_entity_by_params(
                session=self.session,
                model=Item.id,
                conditions=[
                    Item.owner_id == int(self.user.user_id)
                ],
                many=True
            )

    async def get_trade(self):
        self.trade = await get_entity_by_params(
            session=self.session,
            model=ItemTrade,
            conditions=[
                and_(
                    or_(
                        ItemTrade.item_requested_id.in_(self.user_items_ids),
                        ItemTrade.offered_by_user_id == int(self.user.user_id),
                    ),
                        ItemTrade.id == self.trade_id
                )
            ],
            load_relationships=[
                ItemTrade.item_requested,
                ItemTrade.interested_by_owner_item,
                ItemTrade.interested_user
            ],
        )

        if self.trade is None:
            await self.websocket.close()
            return

    async def _send_companion_items(self):
        items = await get_entity_by_params(
            model=Item,
            session=self.session,
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

    async def _get_item_which_your_companion_wants(self):
            second_item = await get_entity_by_params(
                model=Item,
                session=self.session,
                conditions=[Item.id == self.trade.interested_item_id]
            )

            content = [{
                "id": second_item.id,
                "name": second_item.name,
                "image": f"{S3_PUBLIC_URL}/{second_item.s3_url_path}"
            }]

            return content

    async def _get_all_messages(self):
        messages = await get_entity_by_params(
            session=self.session,
            model=Message,
            conditions=[
                Message.trade_id == self.trade_id
            ],
            load_relationships=[Message.sender],
            many=True
        )

        self.messages_in_chat = []

        for message in messages:
            self.messages_in_chat.append({
                "type": "message",
                "text": message.text,
                "sender_image_url": message.sender.image_url,
                "is_my": message.user_id == int(self.user.user_id)
            })
        return self.messages_in_chat

    async def get_new_messages(self):
        messages = await get_entity_by_params(
            session=self.session,
            model=Message,
            conditions=[
                Message.trade_id == self.trade_id,
                Message.id.not_in([int(message["id"]) for message in self.messages_in_chat])
            ],
            load_relationships=[Message.sender],
            many=True
        )

        if messages is not None:
            for message in messages:

                message_info = {
                    "type": "message",
                    "text": message.text,
                    "sender_image_url": message.sender.image_url,
                    "is_my": message.user_id == int(self.user.user_id)
                }

                self.messages_in_chat.append(message_info)

                await self.websocket.send_json(message_info)

    async def get_current_state(self):
        initial_payload = {"type": "initial_data"}

        if self.trade.interested_item_id is None and self.trade.item_requested.owner_id == int(self.user.user_id):
            initial_payload["status"] = "choose item"
            initial_payload["items"] = await self._send_companion_items()

        elif self.trade.interested_item_id is None and self.trade.item_requested.owner_id != int(self.user.user_id):
            initial_payload["status"] = "waiting"

        elif self.trade.interested_item_id is not None and self.trade.is_matched is False and self.trade.item_requested.owner_id == int(self.user.user_id):
            initial_payload["status"] = "waiting"

        elif self.trade.interested_item_id is not None and self.trade.is_matched is False and self.trade.item_requested.owner_id != int(self.user.user_id):

            initial_payload["status"] = "final answer"
            initial_payload["items"] = await self._get_item_which_your_companion_wants()

        else:
            initial_payload["type"] = "active"
            self.status = "active"

        return initial_payload

    async def send_chat(self):

        data = await self.get_current_state()

        if data["type"] == "initial_data":
            await self.websocket.send_json(data)

        if data["type"] == "active":
            if self.messages_in_chat is None:
                await self.websocket.send_json({"type": "active"})
                messages = await self._get_all_messages()
                for message in messages:
                    await self.websocket.send_json(message)
            else:
                await self.get_new_messages()
