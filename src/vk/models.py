from sqlalchemy import Column, BigInteger, String

from src.postgres.models import Base


class User(Base):
    __tablename__ = "vk_users"
    id = Column(BigInteger, primary_key=True)
    fullname = Column(String(255))
    image_url = Column(String(10000))
