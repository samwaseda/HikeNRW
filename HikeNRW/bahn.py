import re
from collections import defaultdict
from datetime import datetime, timedelta

import requests
from pandas import DataFrame

_DATE_RE = re.compile(r"\b\d{1,2}\.\d{1,2}\.\d{4}\b")
_DEPARTURE_RE = re.compile(r"^(?:From|Ab)\s+(\d{1,2}:\d{2})\s+(.+)$", re.IGNORECASE)
_ARRIVAL_RE = re.compile(r"^(?:To|An)\s+(\d{1,2}:\d{2})\s+(.+)$", re.IGNORECASE)
_PLATFORM_RE = re.compile(r",?\s*(?:platform|gleis)\s+(.+)$", re.IGNORECASE)
_TRAIN_RE = re.compile(
    r"^(?:(?:VIA|RRB)\s+)?"
    r"(?:ICE|IC|EC|RE|RB|S|U|STR|Bus|Tram)\s*[\w-]+"
    r"(?:\s*\([^)]*\))?"
    r"(?:\s*/\s*(?:(?:VIA|RRB)\s+)?(?:ICE|IC|EC|RE|RB|S|U|STR|Bus|Tram)\s*[\w-]+"
    r"(?:\s*\([^)]*\))?)*$",
    re.IGNORECASE,
)


def get_date(file_content):
    dates = _DATE_RE.findall(file_content)
    if len(dates) != 1:
        raise ValueError(f"Expected one journey date, found {len(dates)}")
    return datetime.strptime(dates[0], "%d.%m.%Y")


def _parse_stop(line, pattern, journey_date, previous_time):
    match = pattern.match(line.strip())
    if not match:
        raise ValueError(f"Could not parse stop: {line!r}")

    time_text, station_text = match.groups()
    platform_match = _PLATFORM_RE.search(station_text)
    platform = platform_match.group(1).strip() if platform_match else "unknown"
    station = (
        station_text[: platform_match.start()].rstrip(" ,")
        if platform_match
        else station_text.strip()
    )
    if not station:
        raise ValueError(f"Stop has no station name: {line!r}")

    parsed_time = datetime.strptime(
        f"{journey_date:%Y-%m-%d} {time_text}", "%Y-%m-%d %H:%M"
    )
    while previous_time is not None and parsed_time < previous_time:
        parsed_time += timedelta(days=1)
    return station, platform, parsed_time


def get_all_data(file_content):
    journey_date = get_date(file_content)
    all_data = defaultdict(list)
    current_train = None
    departure = None
    previous_time = None

    for line in file_content.splitlines():
        line = line.strip()
        if not line:
            continue

        if _TRAIN_RE.fullmatch(line):
            current_train = line
            continue

        if _DEPARTURE_RE.match(line):
            if departure is not None:
                raise ValueError(f"Departure has no matching arrival: {departure[0]!r}")
            station, platform, timestamp = _parse_stop(
                line, _DEPARTURE_RE, journey_date, previous_time
            )
            departure = (line, station, platform, timestamp, current_train)
            previous_time = timestamp
            continue

        if _ARRIVAL_RE.match(line):
            if departure is None:
                continue
            station, platform, timestamp = _parse_stop(
                line, _ARRIVAL_RE, journey_date, previous_time
            )
            if timestamp == departure[3]:
                raise ValueError(f"Arrival must be after departure: {line!r}")
            all_data["dep_station"].append(departure[1])
            all_data["dep_platform"].append(departure[2])
            all_data["dep_time"].append(departure[3])
            all_data["train"].append(departure[4] or "unknown")
            all_data["arr_station"].append(station)
            all_data["arr_platform"].append(platform)
            all_data["arr_time"].append(timestamp)
            previous_time = timestamp
            departure = None

    if departure is not None:
        raise ValueError(f"Departure has no matching arrival: {departure[0]!r}")
    if not all_data["dep_time"]:
        raise ValueError("No complete journey segments found")
    return DataFrame(all_data)


class Bahn:
    def __init__(self, all_data):
        self.all_data = all_data

    @property
    def container(self):
        container = []
        for index, row in DataFrame(self.all_data).iterrows():
            container.append(
                f"Dep: {row['dep_time'].strftime('%H:%M')} {row['dep_station']} platform {row['dep_platform']} {row['train']}"
            )
            container.append(
                f"Arr: {row['arr_time'].strftime('%H:%M')} {row['arr_station']} platform {row['arr_platform']}"
            )
        return container

    @property
    def starting_time(self):
        return self.all_data["dep_time"].iloc[0]

    @property
    def arrival_time(self):
        return self.all_data["arr_time"].iloc[-1]

    @property
    def meeting_point(self):
        return self.all_data["dep_station"][0]

    def get_schedule(self, html=True):
        if html:
            return (
                "<ol>"
                + "\n".join([f"<li>{s}</li>" for s in self.container])
                + "</ol>"
            )
        else:
            return "\n".join(self.container)

    def get_results(self):
        return {
            "train_schedule": self.get_schedule(html=False),
            "arrival_time": self.arrival_time,
            "starting_time": self.starting_time,
            "meeting_point": self.meeting_point,
        }


def get_train_stations(lat, lon, radius=200, tag="train"):
    if tag == "train":
        tag = '"public_transport"="station"'
    else:
        tag = '"highway"="bus_stop"'
    # Define the Overpass API URL
    overpass_url = "http://overpass-api.de/api/interpreter"

    # Define the Overpass QL query
    overpass_query = f"""
    [out:json];
    (
      node[{tag}](around:{radius},{lat},{lon});
      way[{tag}](around:{radius},{lat},{lon});
      relation[{tag}](around:{radius},{lat},{lon});
    );
    out center;
    """

    # Perform the request
    response = requests.get(overpass_url, params={"data": overpass_query})
    data = response.json()

    # Parse the result
    train_stations = []
    for element in data["elements"]:
        if "tags" in element:
            name = element["tags"].get("name", "Unnamed")
            if name == "Unnamed":
                continue
            lat = element.get("lat", element.get("center", {}).get("lat"))
            lon = element.get("lon", element.get("center", {}).get("lon"))
            train_stations.append({"name": name, "lat": lat, "lon": lon})

    return DataFrame(train_stations)
