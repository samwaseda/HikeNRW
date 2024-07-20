from datetime import datetime


def round_time(d, m):
    return datetime(
        year=d.year,
        month=d.month,
        day=d.day,
        hour=d.hour,
        minute=(d.minute // m) * m
    )
