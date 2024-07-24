from datetime import datetime
from difflib import SequenceMatcher


def round_time(d, m):
    return datetime(
        year=d.year,
        month=d.month,
        day=d.day,
        hour=d.hour,
        minute=(d.minute // m) * m
    )


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def upload_track(komoot_id, date):
    date = date.strftime("%Y%d%m")
    url = f"https://www.sams-studio.com/HIKING/{date}_{komoot_id}.gpx"
    return url
