from enum import StrEnum


class ItemStatusesEnum(StrEnum):
    ACTIVE = "Active"
    NOT_ACTIVE = "Not Active"
    TRADED = "Traded"


class ItemTradeStatusesEnum(StrEnum):
    WAITING = "Waiting"
    COMPLETED = "Completed"
    CANCELED = "Canceled"