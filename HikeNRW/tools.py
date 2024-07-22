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
