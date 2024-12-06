from enum import StrEnum
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
MAX_FILE_SIZE_MB = MAX_FILE_SIZE_BYTES / 1024 / 1024

class AllowedImageFormats(StrEnum):
    JPEG = "image/jpeg"
