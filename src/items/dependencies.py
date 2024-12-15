from fastapi import Form, status, UploadFile, File
from fastapi.responses import JSONResponse

from src.s3_client import MAX_FILE_SIZE_BYTES, AllowedImageFormats, MAX_FILE_SIZE_MB


async def validate_name(name: str = Form(None)):
    if name is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Введите наименование товара"}
        )

    if len(name) > 50 or len(name) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Длина наименования должна быть от 1 до 50 символов"}
        )

    return name


async def validate_description(description: str = Form(None)):
    if description is not None and len(description) > 100:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Длина описания должна быть не более 1000 символов"}
        )

    return description


async def validate_file(file: UploadFile = File(...)):
    if file.size > MAX_FILE_SIZE_BYTES:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"message": f"Размер картинки товара должен быть не более {MAX_FILE_SIZE_MB} мб"}
        )

    if file.content_type != str(AllowedImageFormats.JPEG.value):
        return JSONResponse(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            content={"message": "Неподдержимваемый формат файла. Попробуйте отправить другой файл"})

    return file
