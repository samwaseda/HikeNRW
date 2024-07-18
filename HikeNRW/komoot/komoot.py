from kompy import KomootConnector
import os
from datetime import timedelta

def get_komoot_dict(komoot_id):
    connector = KomootConnector(
        password=os.environ['komoot_psw'],
        email=os.environ['komoot_email'],
    )
    tour = connector.get_tour_by_id(komoot_id)
    tour.generate_gpx_track(authentication=connector.authentication)
    return {
        "elevation_up": tour.elevation_up,
        "elevation_down": tour.elevation_down,
        "difficulty": tour.difficulty.grade,
        "total_duration": timedelta(seconds=tour.total_duration),
        "distance": tour.distance,
        "gpx": tour.gpx_track.to_xml()
    }

