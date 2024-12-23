from pydantic import BaseModel


class DesiredItem(BaseModel):
    item_id: int


class Message(BaseModel):
    text: str