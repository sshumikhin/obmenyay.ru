from typing import Optional
from fastapi import APIRouter, Depends, Request, UploadFile, File, Form, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from vk_id import User as VKUser
from src.items.constants import ItemStatusesEnum
from src.items.models import ItemStatus, Item
from src.items.service import create_item
from src.postgres.api import get_entity_by_params, delete_entity
from src.vk.dependencies import get_current_user
from src.jinja import templates
from src.postgres.session import async_session
from src.s3_client import selectel, S3Client, MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB, AllowedImageFormats
from ssl import SSLError

router = APIRouter(
    prefix="/items"
)


@router.post(
    path="/",
    status_code=status.HTTP_200_OK)
async def append_item_endpoint(
        file: UploadFile = File(...),
        current_user: VKUser = Depends(get_current_user),
        session: AsyncSession = Depends(async_session),
        s3_client: S3Client = Depends(selectel),
        name: str = Form(None),
        description: Optional[str] = Form(None)
):

    if name is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Name is required"}
        )

    if file.size > MAX_FILE_SIZE_BYTES:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"message": f"The file size must not exceed {MAX_FILE_SIZE_MB} MB."}
        )

    if file.content_type != str(AllowedImageFormats.JPEG.value):
        return JSONResponse(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            content={"message": "Unsupported file format"})

    active_item_status = await get_entity_by_params(
        session=session,
        model=ItemStatus,
        conditions=[ItemStatus.name == str(ItemStatusesEnum.ACTIVE.value)]
    )

    if active_item_status is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal server error"})

    item = await create_item(
        session=session,
        name=name,
        description=description,
        vk_user_id=int(current_user.user_id),
        s3_path="",
        status=active_item_status
    )

    item.s3_url_path = f"users/{current_user.user_id}/items/{item.id}"

    try:
        await s3_client.upload_file(
            file_stream=file.file,
            file_name=item.s3_url_path)

        await session.commit()

    except Exception as e:
        print(str(e))
        # TODO: отправлять в логи
        await session.rollback()


        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal server error"}
        )

    return {"id": item.id,
            "name": item.name,
            "description": item.description}


@router.delete(path="/{item_id}")
async def delete_item_endpoint(
        item_id: int,
        current_user: VKUser = Depends(get_current_user),
        session: AsyncSession = Depends(async_session),
        s3_client: S3Client = Depends(selectel),
):

    active_item_status = await get_entity_by_params(
        session=session,
        model=ItemStatus,
        conditions=[ItemStatus.name == str(ItemStatusesEnum.ACTIVE.value)]
    )

    item = await get_entity_by_params(
        session=session,
        model=Item,
        conditions=[Item.id == item_id, Item.owner_id == int(current_user.user_id)],
    )

    if item is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Item was not found"}
        )
    try:
        await s3_client.delete_file(object_name=item.s3_url_path)
        await delete_entity(
            session=session,
            entity=item
        )
        await session.commit()
    except Exception as e:
        await session.rollback()


@router.patch(path="/")
async def update_item_endpoint():
    pass


@router.post(path="/skip")
async def skip_item_endpoint():
    pass


@router.post(path="/like")
async def like_item_endpoint():
    pass


@router.get(path="/for-trade")
async def get_items_for_trade_endpoint(
        request: Request,
        # vk_user: VKUser = Depends(get_current_user),
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
async def get_my_profile(
        request: Request,
        vk_user: VKUser = Depends(get_current_user),
        session: AsyncSession = Depends(async_session),
):

    active_item_status = await get_entity_by_params(
        session=session,
        model=ItemStatus,
        conditions=[ItemStatus.name == str(ItemStatusesEnum.ACTIVE.value)]
    )

    if active_item_status is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal server error"})

    items = await get_entity_by_params(
        session=session,
        model=Item,
        conditions=[Item.owner_id == int(vk_user.user_id),
                    Item.status_id == active_item_status.id],
        many=True
    )

    return templates.TemplateResponse(
        "personal_cabinet.html",
        {
            "request": request,
            "personal_things": [{
                "id": item.id,
                "name": item.name,
                "description": item.description
            } for item in items]
        }
    )