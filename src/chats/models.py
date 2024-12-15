from sqlalchemy import Column, BigInteger

from src.postgres.models import Base


class Chat(Base):
    __tablename__ = "chats"
    id = Column(BigInteger, primary_key=True)

