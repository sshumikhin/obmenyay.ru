from .api import S3Client
from .config import *
from .constants import *


__all__ = [
    "selectel",
    "S3Client",
    "MAX_FILE_SIZE_BYTES",
    "MAX_FILE_SIZE_MB",
    "AllowedImageFormats"]


selectel = S3Client(
        access_key=ACCESS_TOKEN,
        secret_key=SECRET_TOKEN,
        endpoint_url=ENDPOINT_URL,
        bucket_name=BUCKET_NAME
    )
