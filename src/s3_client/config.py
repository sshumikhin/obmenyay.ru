from src.utils import getenv

ACCESS_TOKEN = getenv("S3_ACCESS_TOKEN")
SECRET_TOKEN = getenv("S3_SECRET_TOKEN")
ENDPOINT_URL = getenv("S3_ENDPOINT_URL")
BUCKET_NAME = getenv("S3_BUCKET_NAME")
PUBLIC_URL = getenv("S3_PUBLIC_URL")