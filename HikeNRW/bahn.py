from datetime import datetime, timedelta
from collections import defaultdict
import re
from pandas import DataFrame


def remove_time(txt):
    new_txt = []
    passed_gl = False
    for tt in txt.split():
        if tt == "Gl.":
            passed_gl = True
        elif (tt.endswith("h") or tt.endswith("min")) and passed_gl:
            return " ".join(new_txt)
        new_txt.append(tt)
    return " ".join(new_txt)


def get_date(file_content):
    content = re.findall("\d\d\.\d\d\.\d{4}", file_content)
    assert len(content) == 1, "Date not identified"
    try:
        return datetime.strptime(content[0], "%d.%m.%Y")
    except ValueError as e:
        print(e.args)
        pass


def get_all_data(file_content):
    def get_train_station(line):
        station = re.findall("\d{1,2}:\d\d (.*),", line)
        assert len(station) == 1, station
        return station[0]

    def get_platform(line):
        pf = re.findall("platform\s*(.*)", line)
        if len(pf) == 0:
            return "XXX"
        assert len(pf) == 1
        return pf[0]

    def get_time(line):
        t = re.findall("(\d{1,2}:\d\d)", line)
        return t[0]
    all_data = defaultdict(list)
    for chunk in file_content.split("\n\n")[1:-1]:
        content = chunk.split("\n")
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
    return all_data


class Bahn:
    @property
    def content(self):
        content = self.file_content.split("\n\n")[1:-1]
        all_stops = []
        for c in content:
            all_stops.extend(re.findall("\d\d:\d\d (.*),", c))
        assert len(all_stops) % 2 == 0, \
            "Arr. and Dep. not correctly detected {}".format(all_stops)
        return all_stops

    @property
    def container(self):
        container = []
        for index, row in DataFrame(self.all_data).iterrows():
            container.append(f"Dep: {row['dep_time']} {row['dep_station']} platform {row['dep_platform']} {row['train']}")
            container.append(f"Arr: {row['arr_time']} {row['arr_station']} platform {row['arr_platform']}")
        return container

    @property
    def starting_time(self):
        value = [int(dd) for dd in self.all_data["dep_time"][0].split(":")]
        return self.date + timedelta(hours=value[0], minutes=value[1])

    @property
    def arrival_time(self):
        value = [int(dd) for dd in self.all_data["arr_time"][-1].split(":")]
        return self.date + timedelta(hours=value[0], minutes=value[1])

    @property
    def meeting_time(self):
        zeit = self.starting_time - timedelta(minutes=15)
        return self.date + timedelta(hours=zeit.hour, minutes=zeit.minute // 15 * 15)

    @property
    def meeting_point(self):
        return self.all_data["dep_station"][0]

    def get_schedule(self, html=True):
        if html:
            return '<ol>' + '\n'.join(['<li>{}</li>'.format(s) for s in self.container]) + '</ol>'
        else:
            return '\n'.join(self.container)

