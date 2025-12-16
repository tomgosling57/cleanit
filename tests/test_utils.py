from datetime import datetime, timedelta

def get_future_date(days: int) -> str:
    future_date = datetime.now() + timedelta(days=days)
    return future_date.strftime("%Y-%m-%d")

def get_future_time(hours: int) -> str:
    future_time = datetime.now() + timedelta(hours=hours)
    return future_time.strftime("%H:%M")