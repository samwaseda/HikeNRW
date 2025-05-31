from datetime import datetime, timedelta
from collections import defaultdict
import re
from pandas import DataFrame
import requests
from hashlib import sha256

from HikeNRW.HikeNRW.tools import round_time


def get_date(file_content):
    content = re.findall("\d\d\.\d\d\.\d{4}", file_content)
    assert len(content) == 1, f"Date not identified {file_content}"
    try:
        return datetime.strptime(content[0], "%d.%m.%Y")
    except ValueError as e:
        print(e.args)
        pass


def get_all_data(file_content):
    date = get_date(file_content)
    def get_train_station(line):
        station = re.findall(r"\d{1,2}:\d\d (.*?)(?:, platform|$)", line)
        assert len(station) == 1, str(station) + line
        return station[0]

    def get_platform(line):
        pf = re.findall("platform\s*(.*)", line)
        if len(pf) == 0:
            return "unknown"
        assert len(pf) == 1
        return pf[0]

    def get_time(line, day=date):
        t = re.findall("(\d{1,2}:\d\d)", line)
        return datetime.strptime(day.strftime(f"%Y/%m/%d {t[0]}"), "%Y/%m/%d %H:%M")

    all_data = defaultdict(list)
    for chunk in file_content.split("\n\n")[1:-1]:
        content = chunk.replace(" Gleis ", " platform ").split("\n")
        data = {
            "dep_station": get_train_station(content[-2]),
            "arr_station": get_train_station(content[-1]),
            "dep_platform": get_platform(content[-2]),
            "arr_platform": get_platform(content[-1]),
            "train": content[0],
            "dep_time": get_time(content[-2]),
            "arr_time": get_time(content[-1]),
        }
        for k, v in data.items():
            all_data[k].append(v)

    with open(f"../tests/bahn/{sha256(file_content.encode()).hexdigest()}.txt", "w") as f:
        f.write(file_content)

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
            container.append(f"Arr: {row['arr_time'].strftime('%H:%M')} {row['arr_station']} platform {row['arr_platform']}")
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
            return '<ol>' + '\n'.join(['<li>{}</li>'.format(s) for s in self.container]) + '</ol>'
        else:
            return '\n'.join(self.container)

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
    response = requests.get(overpass_url, params={'data': overpass_query})
    data = response.json()

    # Parse the result
    train_stations = []
    for element in data['elements']:
        if 'tags' in element:
            name = element['tags'].get('name', 'Unnamed')
            if name == "Unnamed":
                continue
            lat = element.get('lat', element.get('center', {}).get('lat'))
            lon = element.get('lon', element.get('center', {}).get('lon'))
            train_stations.append({
                'name': name,
                'lat': lat,
                'lon': lon
            })

    return DataFrame(train_stations)
