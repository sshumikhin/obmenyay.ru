from typing import Optional
from pydantic import BaseModel


class GetTokens(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None