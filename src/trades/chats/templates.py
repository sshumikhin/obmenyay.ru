from typing import List, Dict, Optional
from fastapi import APIRouter, Request, Depends
from src.jinja import templates
from .router import router


@router.get("/")
async def get_chats(request: Request, trade_id: Optional[int] = None):
    if trade_id is None:
        return templates.TemplateResponse("chats.html", {"request": request})

    return templates.TemplateResponse("messages.html", {"request": request, "trade_id": trade_id})
