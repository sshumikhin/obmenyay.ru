# Standart

# Third party
from fastapi import FastAPI, Request, Depends
from starlette.middleware.cors import CORSMiddleware

from src.vk.constants import JWTTokens
from src.vk.router import router as vk_router
from src.items.router import router as items_router
from src.chats.router import router as chats_router
# First party
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from vk_id import configure_app as vk_id_app_configure
from src.vk.config import *
from src.vk.exceptions import UserIsNotAuthenticated

app = FastAPI(
    title="Обменяй.ру",
    docs_url="/docs",
    redoc_url=None
)

app.mount(
    path="/static",
    app=StaticFiles(directory="static", html=True),
    name="static"
)

vk_id_app_configure(
    app_name=APP_NAME,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    client_access_key=CLIENT_ACCESS_KEY,
    profile=REDIRECT_URI
)


app.include_router(vk_router)
app.include_router(items_router)
app.include_router(chats_router)


@app.exception_handler(UserIsNotAuthenticated)
async def authentication_exception_handler(
        request: Request,
        exc: UserIsNotAuthenticated
):
    response = RedirectResponse("/vk/login")
    response.delete_cookie(str(JWTTokens.REFRESH.value))
    response.delete_cookie(str(JWTTokens.ACCESS.value))
    response.delete_cookie("state")
    response.delete_cookie("device_id")
    return response


@app.get("/")
async def get_main_page():
    return RedirectResponse("/items/for-trade")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# TODO: Убрать использование литеральных значений
# TODO: добавить версионирование
# TODO: добавить общие ошибки в экземлпяр приложения
