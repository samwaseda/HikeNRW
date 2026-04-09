import os
import re
from kompy import KomootConnector
from datetime import timedelta


def extract_komoot_id(text):
    # Define the regular expression pattern for 9 to 11 digit numbers
    pattern = r"\b\d{9,11}\b"
    # Find all matches in the text
    matches = re.findall(pattern, text)
    if len(matches) == 0:
        raise ValueError("There is no Komoot ID in the string")
    elif len(matches) > 1:
        raise ValueError("Multiple Komoot ID got detected")
    return matches[0]


def extract_komoot_url(text):
    matches = re.findall(r"https?://(?:www\.)?komoot[^\s]*", text)
    if len(matches) == 0:
        raise ValueError("No komoot link found")
    return matches[0]


def get_komoot_dict(komoot_message):
    komoot_id = extract_komoot_id(komoot_message)
    connector = KomootConnector(
        password=os.environ["komoot_psw"],
        email=os.environ["komoot_email"],
    )
    tour = connector.get_tour_by_id(komoot_id)
    tour.vector_map_image.load_image()
    tour.generate_gpx_track(authentication=connector.authentication)
    return {
        "id": komoot_id,
        "name": tour.name,
        "elevation_up": tour.elevation_up,
        "elevation_down": tour.elevation_down,
        "difficulty": tour.difficulty.grade,
        "total_duration": timedelta(seconds=tour.total_duration),
        "distance": tour.distance,
        "gpx": tour.gpx_track.to_xml(),
        "url": f"https://www.komoot.com/de-de/tour/{tour.id}",
        "tour": tour,
        "url": extract_komoot_url(komoot_message),
        "vector_image": tour.vector_map_image.image,
        "links_dict": tour.links_dict,
    }
