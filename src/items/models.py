from sqlalchemy import (
    Column,
    String,
    BigInteger, Integer, ForeignKey
)

from src.postgres.models import Base


class ItemStatus(Base):
    __tablename__ = "item_statuses"
    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String(255))


class Item(Base):
    __tablename__ = "items"
    id = Column(BigInteger, primary_key=True, unique=True, autoincrement=True)
    name = Column(String(255))
    description = Column(String(255), nullable=True)
    owner_id = Column(BigInteger)
    status_id = Column(Integer, ForeignKey(ItemStatus.id))
    s3_url_path = Column(String(255))


class ItemTradeStatus(Base):
    __tablename__ = "item_trade_statuses"
    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String(255))


class ItemTrade(Base):
    __tablename__ = "item_trades"
    id = Column(BigInteger, primary_key=True, unique=True)
    item_offered_id = Column(BigInteger, ForeignKey(Item.id))
    item_requested_id = Column(BigInteger, ForeignKey(Item.id))


# sqlalchemy.exc.InvalidRequestError: Can't copy ForeignKey object which refers to non-table bound Column Column(None, Integer(), table=None, primary_key=True, nullable=False)