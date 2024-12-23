from sqlalchemy import (
    Column,
    BigInteger,
    ForeignKey,
    Text,
    Boolean,
    UniqueConstraint,
    DateTime
)
from sqlalchemy.orm import relationship

from src.items.models import Item
from src.postgres.models import Base
from src.postgres.utils import utcnow_without_tzinfo
from src.vk.models import User


class ItemTrade(Base):
    __tablename__ = "item_trades"

    id = Column(BigInteger, primary_key=True, unique=True)
    item_requested_id = Column(BigInteger, ForeignKey(Item.id), nullable=False)
    offered_by_user_id = Column(BigInteger, ForeignKey(User.id), nullable=False)
    created_at_utc = Column(DateTime, default=utcnow_without_tzinfo)
    interested_item_id = Column(BigInteger, ForeignKey(Item.id), nullable=True)
    is_matched = Column(Boolean, default=False)

    item_requested = relationship("Item", foreign_keys=[item_requested_id])
    interested_by_owner_item = relationship("Item", foreign_keys=[interested_item_id])
    interested_user = relationship("User", foreign_keys=[offered_by_user_id])

    __table_args__ = (
        UniqueConstraint("offered_by_user_id", "item_requested_id", name="user_trade_items_unique"),
    )


class Message(Base):
    __tablename__ = "messages"
    id = Column(BigInteger, primary_key=True)
    trade_id = Column(BigInteger, ForeignKey("item_trades.id"))
    user_id = Column(BigInteger, ForeignKey(User.id))
    text = Column(Text)
    is_seen = Column(Boolean, default=False)

    sender = relationship("User")
