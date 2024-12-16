from sqlalchemy import (
    Column,
    BigInteger,
    ForeignKey,
    Text
)

from src.postgres.models import Base


class Message(Base):
    __tablename__ = "messages"
    id = Column(BigInteger, primary_key=True)
    trade_id = Column(BigInteger, ForeignKey("item_trades.id"))
    user_id = Column(BigInteger)
    text = Column(Text)
