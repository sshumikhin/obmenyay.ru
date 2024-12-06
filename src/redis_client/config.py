from src.utils import getenv


__all__ = [
    "CONNECTION_URL",
]


HOST = getenv("REDIS_HOST")
PORT = getenv("REDIS_PORT")
CONNECTION_URL = F"redis://{HOST}:{PORT}/0"