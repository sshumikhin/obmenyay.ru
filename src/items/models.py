from sqlalchemy import (
    Column,
    String,
    BigInteger,
    ForeignKey,
    Boolean
)
from sqlalchemy.orm import relationship

from src.postgres.models import Base


class Item(Base):
    __tablename__ = "items"
    id = Column(BigInteger, primary_key=True, unique=True, autoincrement=True)
    name = Column(String(255))
    description = Column(String(255), nullable=True)
    owner_id = Column(BigInteger)
    s3_url_path = Column(String(255))
    is_available = Column(Boolean, default=True)

    seens = relationship(argument="UserSeenItem", back_populates="item", cascade="all, delete")
    # trades = relationship(argument="ItemTrade", back_populates="item_offered", cascade="all, delete")


class UserSeenItem(Base):
    __tablename__ = "user_seen_items"
    id = Column(BigInteger, primary_key=True, unique=True)
    user_id = Column(BigInteger)
    item_id = Column(BigInteger, ForeignKey(Item.id))

    item = relationship(argument="Item", back_populates="seens")


# class ItemTrade(Base):
#     __tablename__ = "item_trades"
#     id = Column(BigInteger, primary_key=True, unique=True)
#     item_offered_id = Column(BigInteger, ForeignKey(Item.id), nullable=False)
#     item_requested_id = Column(BigInteger, ForeignKey(Item.id), nullable=False)
#     offered_by_user_id = Column(BigInteger, nullable=False)
#     # trade_status_id = Column(Integer, ForeignKey('item_trade_statuses.id'), nullable=False)
#     # is_requested_agreed = Column(Integer, default=0)
#     # created_at_utc = Column(DateTime(timezone=True), server_default=func.now())
#
#     item_requested = relationship(argument="Item", back_populates="trades")
#     item_offered = relationship(argument="Item", back_populates="trades")
