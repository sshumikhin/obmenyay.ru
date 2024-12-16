import vk_id
from fastapi import (
    APIRouter,
    status,
    Request, Depends
)

from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from vk_id import (
    generate_pkce,
    get_app_configuration,
    Scopes,
    exchange_code,
    Error as ExchangeCodeError
)

from src.vk.constants import JWTTokens
from src.vk.dependencies import get_tokens
from src.jinja import templates
from src.redis_client.connection import redis_client
from src.vk.schemas import GetTokens
from .models import User
from .services import create_user
from ..postgres.api import get_entity_by_params
from ..postgres.session import async_session

router = APIRouter(
    prefix="/vk",
    tags=["Oauth2 VK"],


)


@router.get(
    path="/login",
    summary="Регистрация нового пользователя",
)
async def get_login_page(
        request: Request,
        tokens=Depends(get_tokens)
):

    if tokens.access_token is not None or tokens.refresh_token is not None:
        return RedirectResponse("/")

    app_config = get_app_configuration()

    pkce = generate_pkce(
        scopes=[Scopes.DEFAULT.value]
    )

    payload = {
        "vk_app_id": int(app_config.client_id),
        "redirect_url": "https://obmenyay-ru.ru/vk/oauth2/token",
        "code_challenge": pkce.code_challenge,
        "code_verifier": pkce.code_verifier,
        "scope": pkce.scopes,
        "app_name": app_config.app_name
    }

    await redis_client.set(
        key=pkce.state,
        value=payload
    )

    payload["request"] = request
    payload["state"] = pkce.state

    del payload["code_verifier"]

    return templates.TemplateResponse(
        "login.html",
        payload
    )


@router.get(
    path="/oauth2/token",
    status_code=status.HTTP_200_OK,
    response_class=RedirectResponse,
)
async def get_code_state_device_id(
        request: Request,
        tokens: GetTokens = Depends(get_tokens),
        session: AsyncSession = Depends(async_session)
):
    authenticated_response = RedirectResponse("/")

    if bool(tokens.model_dump(exclude_none=True)):
        return authenticated_response

    state = request.query_params.get("state", False)
    code = request.query_params.get("code", False)
    device_id = request.query_params.get("device_id", False)

    if not(state and code and device_id):
        return authenticated_response

    vk_id_auth_params = await redis_client.connection.hgetall(state)

    if vk_id_auth_params is None:
        return authenticated_response

    tokens = await exchange_code(
            code_verifier=vk_id_auth_params["code_verifier"],
            redirect_uri_tag="profile",
            code=code,
            device_id=device_id,
            state=state
    )
    await redis_client.delete(state)

    if isinstance(tokens, ExchangeCodeError):
        return authenticated_response

    success_response = RedirectResponse("https://obmenyay-ru.ru/items/my")

    success_response.set_cookie(
        key=str(JWTTokens.ACCESS.value),
        value=tokens.access_token,
        httponly=True,
        secure=True,
        samesite="none",
        expires=tokens.expires_in
    )

    success_response.set_cookie(
        key=str(JWTTokens.REFRESH.value),
        value=tokens.refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        expires=432000
    )

    success_response.set_cookie(
        key="device_id",
        value=device_id,
        httponly=True,
        secure=True,
        samesite="none",
        expires=432000
    )

    success_response.set_cookie(
        key="state",
        value=state,
        httponly=True,
        secure=True,
        samesite="none",
        expires=432000
    )

    vk_user = await vk_id.get_user_public_info(
        access_token=tokens.access_token
    )

    db_user = await get_entity_by_params(
        session=session,
        model=User,
        conditions=[
           User.id == int(vk_user.user_id)
        ]
    )

    if db_user is None:
        await create_user(
            session=session,
            user_id=int(vk_user.user_id),
            fullname=f"{vk_user.first_name} {vk_user.last_name}",
            image_url=vk_user.avatar
        )
    else:
        db_user.fullname = f"{vk_user.first_name} {vk_user.last_name}"
        db_user.image_url = vk_user.image_url

    await session.commit()

    return success_response


# @router.post(path="/oauth2/token/logout")
# async def logout_token_endpoint():
#     """
#     POST https://id.vk.com/oauth2/logout
#
#     Content-Type: application/x-www-form-urlencoded
#
#     client_id=<идентификатор приложения>
#     & access_token=<Access token пользователя>
#     """
#     pass

# @router.post(path="/token/revoke")
# async def revoke_token_endpoint():
#     # POST
#     # https: // id.vk.com / oauth2 / revoke
#     #
#     # Content - Type: application / x - www - form - urlencoded
#     #
#     # client_id = < идентификатор
#     # приложения >
#     # & access_token = < Access
#     # token
#     # пользователя >


# @router.post(path="/oauth2/token/refresh")
# async def refresh_token_endpoint():
#     """
#     POST https://id.vk.com/oauth2/auth
#
#     Content-Type: application/x-www-form-urlencoded
#
#     grant_type=refresh_token
#     & refresh_token=<токен для обмена>
#     & client_id=<идентификатор приложения>
#     & device_id=<идентификатор устройства>
#     & state=<произвольная строка состояния>
#     & [scope=<список доступов>]
#     """
#     pass