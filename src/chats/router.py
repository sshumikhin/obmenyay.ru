from fastapi import APIRouter, Request
from src.jinja import templates

router = APIRouter(
    prefix="/chats"
)


@router.get("/")
async def get_my_active_chats(request: Request):
    return templates.TemplateResponse(
        "messages.html",
        {"request": request}
    )
