from fastapi import Request
from fastapi.responses import RedirectResponse

from .exceptions import UserIsNotAuthenticated
from .schemas import GetTokens
from .constants import JWTTokens
from vk_id import User, get_user_public_info


async def get_tokens(request: Request) -> GetTokens:
    return GetTokens(
        access_token=request.cookies.get(str(JWTTokens.ACCESS.value)),
        refresh_token=request.cookies.get(str(JWTTokens.REFRESH.value)),
)

async def get_current_user(request: Request) -> User | RedirectResponse:

    tokens = await get_tokens(request)

    if not bool(tokens.model_dump(exclude_none=True)):
        raise UserIsNotAuthenticated

    # TODO: Брать из кэша данные пользователя
    if tokens.access_token is not None:
        vk_server_response = await get_user_public_info(
            access_token=tokens.access_token
        )

        if isinstance(vk_server_response, User):
            return vk_server_response

        else:
            # TODO: если не были найдены в кэше, делать запрос.
            raise UserIsNotAuthenticated

    # TODO: продумать логику обновления кода
    else:
        raise UserIsNotAuthenticated
