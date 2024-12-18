from sqlalchemy import (
    Column,
    String,
    BigInteger,
    ForeignKey,
    Boolean,
    DateTime, UniqueConstraint
)
from sqlalchemy.orm import relationship

from src.postgres.models import Base
from src.postgres.utils import utcnow_without_tzinfo
from src.vk.models import User


class Item(Base):
    __tablename__ = "items"
    id = Column(BigInteger, primary_key=True, unique=True, autoincrement=True)
    name = Column(String(255))
    description = Column(String(255), nullable=True)
    owner_id = Column(BigInteger, ForeignKey(User.id))
    s3_url_path = Column(String(255))
    is_available = Column(Boolean, default=True)

    owner = relationship(argument="User")
    seens = relationship(argument="UserSeenItem", back_populates="item", cascade="all, delete")
    trades = relationship(argument="ItemTrade", back_populates="item_requested", cascade="all, delete")


class UserSeenItem(Base):
    __tablename__ = "user_seen_items"
    id = Column(BigInteger, primary_key=True, unique=True)
    user_id = Column(BigInteger)
    item_id = Column(BigInteger, ForeignKey(Item.id))

    item = relationship(argument="Item", back_populates="seens")

    __table_args__ = (
        UniqueConstraint("user_id", "item_id", name="user_seen_items_unique"),
    )


class ItemTrade(Base):
    __tablename__ = "item_trades"
    id = Column(BigInteger, primary_key=True, unique=True)
    item_requested_id = Column(BigInteger, ForeignKey(Item.id), nullable=False)
    offered_by_user_id = Column(BigInteger, ForeignKey(User.id), nullable=False)
    created_at_utc = Column(DateTime, default=utcnow_without_tzinfo)
    is_matched = Column(Boolean, default=False)

    item_requested = relationship(argument="Item", back_populates="trades")
    interested_user = relationship(argument="User")

    __table_args__ = (
        UniqueConstraint("offered_by_user_id", "item_requested_id", name="user_trade_items_unique"),
    )
