from pydantic import BaseModel


class Delete_item(BaseModel):
    item_id: int