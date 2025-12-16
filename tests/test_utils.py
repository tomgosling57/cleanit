from datetime import datetime, timedelta
from config import DATETIME_FORMATS

def get_future_date(days: int) -> str:
    future_date = datetime.now() + timedelta(days=days)
    return future_date.strftime(DATETIME_FORMATS["DATE_FORMAT"])

def get_future_time(hours: int) -> str:
    future_time = datetime.now() + timedelta(hours=hours)
    return future_time.strftime(DATETIME_FORMATS["TIME_FORMAT"])