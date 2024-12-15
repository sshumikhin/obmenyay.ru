from typing import Optional
from fastapi import APIRouter, Depends, Request, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from vk_id import User as VKUser
from src.items.models import Item, UserSeenItem
from src.items.service import create_item, skip_item
from src.postgres.api import get_entity_by_params, delete_entity
from src.vk.dependencies import get_current_user
from src.jinja import templates
from src.postgres.session import async_session
from src.s3_client import selectel, S3Client, MAX_FILE_SIZE_MB, PUBLIC_URL as S3_PUBLIC_URL
from .dependencies import validate_name, validate_description, validate_file
from .schemas import Delete_item
from PIL import Image, ImageFilter
import io



router = APIRouter(
    prefix="/items"
)


@router.post(
    summary="Добавить новый предмет",
    path="/",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Предмет был успешно добавлен",
            "content": {
                "application/json": {
                    "examples": {
                        "item_successfully_created": {
                            "summary": "Предмет был успешно добавлен",
                            "value": {"id": 1234,
                                      "name": "Карандаш",
                                      "description": "Простой"
                                      }
                        }
                    }
                }
            },
        400: {
            "description": "Поле name не прошло валидацию",
            "content": {
                "application/json": {
                    "examples": {
                        "empty_field": {
                            "summary": "Поле является пустым",
                            "value": {"message": "Введите наименование товара"}
                        },
                        "inccorrect_length_of_value": {
                            "summary": "Неккоретная длина наименования товара",
                            "value": {"message": "Длина наименования должна быть от 1 до 50 символов"}
                        }
                    }
                }
            }
        },
        413: {
            "description": "Большой вес картинки",
                "content": {
                    "application/json": {
                        "examples": {
                            "item_picture_too_big": {
                                "summary": "Большой вес картинки",
                                "value": {"message": f"Размер картинки товара должен быть не более {MAX_FILE_SIZE_MB} мб"}
                            }
                        }
                    }
                }
            },
        415: {
            "description": "Неподдерживаемый формат картинки",
                "content": {
                    "application/json": {
                        "examples": {
                            "unsupported_image_format": {
                                "summary": "Неподдерживаемый формат картинки",
                                "value": {"message": "Неподдержимваемый формат файла. Попробуйте отправить другой файл"}
                            }
                        }
                    }
                }
            }
        }
    }
)
async def append_item_endpoint(
        name: str = Depends(validate_name),
        description: Optional[str] = Depends(validate_description),
        file: UploadFile = Depends(validate_file),
        current_user: VKUser = Depends(get_current_user),
        session: AsyncSession = Depends(async_session),
        s3_client: S3Client = Depends(selectel),
):
    item = await create_item(
        session=session,
        name=name,
        description=description,
        vk_user_id=int(current_user.user_id),
        s3_path="",
    )

    contents = await file.read()
    img = Image.open(io.BytesIO(contents))

    format = img.format

    width, height = img.size

    max_size = 500
    ratio = min(max_size / width, max_size / height)
    new_width = int(width * ratio)
    new_height = int(height * ratio)

    img = img.resize((new_width, new_height))

    new_width, new_height = 500, 300
    background_color = (255, 255, 255)
    new_img = Image.new('RGB', (new_width, new_height), background_color)

    offset_x = (new_width - img.width) // 2
    offset_y = (new_height - img.height) // 2

    new_img.paste(img, box =(offset_x, offset_y))

    output = io.BytesIO()

    new_img.save(
        output,
        format=format,
        quality=100
    )

    output.seek(0)

    item.s3_url_path = f"/users/{current_user.user_id}/items/{item.id}"

    try:
        await s3_client.upload_file(
            file_stream=output.getvalue(),
            file_name=item.s3_url_path)

        await session.commit()

    except Exception as e:
        print(str(e))
        # TODO: отправлять в логи
        await session.rollback()

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Внутренняя ошибка сервера"}
        )

    return {"id": item.id,
            "name": item.name,
            "description": item.description}


@router.delete(
    summary="Удалить товар",
    path="/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        200: {
            "description": "Предмет был удалён",
            "content": {
                "application/json": {
                    "examples": {
                        "item_successfully_deleted": {
                            "summary": "Предмет был удалён",
                            "value": {"message": "ОК"}
                        }
                    }
                }
            },
        400: {
            "description": "Поле name не прошло валидацию",
            "content": {
                "application/json": {
                    "examples": {
                        "empty_field": {
                            "summary": "Поле является пустым",
                            "value": {"message": "Введите наименование товара"}
                        },
                        "inccorrect_length_of_value": {
                            "summary": "Неккоретная длина наименования товара",
                            "value": {"message": "Длина наименования должна быть от 1 до 50 символов"}
                        }
                    }
                }
            }
        },
        413: {
            "description": "Большой вес картинки",
                "content": {
                    "application/json": {
                        "examples": {
                            "item_picture_too_big": {
                                "summary": "Большой вес картинки",
                                "value": {"message": f"Размер картинки товара должен быть не более {MAX_FILE_SIZE_MB} мб"}
                            }
                        }
                    }
                }
            },
        404: {
            "description": "Предмет не был найден",
                "content": {
                    "application/json": {
                        "examples": {
                            "item_was_not_found": {
                                "summary": "Предмет не был найден",
                                "value": {"message": "Предмет не был найден"}
                            }
                        }
                    }
                }
            }
        }
    }
)
async def delete_item_endpoint(
        item: Delete_item,
        current_user: VKUser = Depends(get_current_user),
        session: AsyncSession = Depends(async_session),
        s3_client: S3Client = Depends(selectel),
):

    item_id = item.item_id

    item = await get_entity_by_params(
        session=session,
        model=Item,
        conditions=
        [
            Item.id == item_id,
            Item.owner_id == int(current_user.user_id)
        ],
    )

    if item is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Предмет не был найден"}
        )
    try:
        await s3_client.delete_file(object_name=item.s3_url_path)

        await delete_entity(
            session=session,
            entity=item
        )
        await session.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "ОК"}
        )
    except Exception as e:
        await session.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Внутренняя ошибка сервера"}
        )


@router.get(
    summary="Получить новую партию товаров для обмена",
    path="/"
)
async def get_items_endpoint(
        vk_user: VKUser = Depends(get_current_user),
        session: AsyncSession = Depends(async_session)
):
    watched_items_ids = await get_entity_by_params(
        session=session,
        model=UserSeenItem.item_id,
        conditions=
        [
            UserSeenItem.user_id == int(vk_user.user_id)
        ],
        many=True
    )

    unwatched_items = await get_entity_by_params(
        session=session,
        model=Item,
        conditions=[
            Item.owner_id != int(vk_user.user_id),
            Item.id.not_in(watched_items_ids),
            Item.is_available
        ],
        limit=30,
        many=True
    )

    content = []
    for item in unwatched_items:
        content.append(
            {
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "s3_url_path": f"{S3_PUBLIC_URL}/{item.s3_url_path}"
            }
        )

    return content


@router.get(
    path="/{item_id}/skip",
    status_code=status.HTTP_204_NO_CONTENT
)
async def skip_item_endpoint(
        item_id: int,
        vk_user: VKUser = Depends(get_current_user),
        session: AsyncSession = Depends(async_session)
):
    await skip_item(
        session=session,
        item_id=item_id,
        vk_user_id=int(vk_user.user_id)
    )


@router.get(path="/{item_id}/like")
async def like_item_endpoint(
        item_id: int,
        vk_user: VKUser = Depends(get_current_user),
        session: AsyncSession = Depends(async_session)
):
    user_items = await get_entity_by_params(
        session = session,
        model= Item.id,
        conditions=[Item.owner_id == int(vk_user.user_id)],
    )

    if user_items is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "У вас нет товаров, чтобы начать обмен"}
        )




@router.get(
    path="/for-trade"
)
async def get_items_for_trade_endpoint(
        request: Request,
        vk_user: VKUser = Depends(get_current_user),
        session: AsyncSession = Depends(async_session),
):

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request}
    )


@router.get(
    path="/my",
    include_in_schema=False
)
async def get_my_items_endpoint(
        request: Request,
        vk_user: VKUser = Depends(get_current_user),
        session: AsyncSession = Depends(async_session),
):

    items = await get_entity_by_params(
        session=session,
        model=Item,
        conditions=[Item.owner_id == int(vk_user.user_id)],
        many=True
    )

    return templates.TemplateResponse(
        "personal_cabinet.html",
        {
            "request": request,
            "username": f"{vk_user.first_name} {vk_user.last_name}",
            "personal_things": [{
                "id": item.id,
                "name": item.name,
                "description": item.description
            } for item in items]
        }
    )
