import pytz
from datetime import datetime

def utcnow_without_tzinfo():
    return datetime.now(pytz.utc).replace(tzinfo=None)
