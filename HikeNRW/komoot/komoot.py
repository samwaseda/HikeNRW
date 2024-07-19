from kompy import KomootConnector
import os
from datetime import timedelta


def get_html(komoot_id):
    f_dir = os.path.dirname(__file__)
    with open(os.path.join(f_dir, "html.template"), "r") as f:
        return f.readline().replace("TOURID", str(komoot_id))


def get_komoot_dict(komoot_id):
    connector = KomootConnector(
        password=os.environ['komoot_psw'],
        email=os.environ['komoot_email'],
    )
    tour = connector.get_tour_by_id(komoot_id)
    tour.generate_gpx_track(authentication=connector.authentication)
    return {
        "name": tour.name,
        "elevation_up": tour.elevation_up,
        "elevation_down": tour.elevation_down,
        "difficulty": tour.difficulty.grade,
        "total_duration": timedelta(seconds=tour.total_duration),
        "distance": tour.distance,
        "gpx": tour.gpx_track.to_xml(),
        "url": f"https://www.komoot.com/de-de/tour/{tour.id}",
        "html": get_html(tour.id),
    }

