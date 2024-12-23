from pydantic import BaseModel


class DesiredItem(BaseModel):
    item_id: int
