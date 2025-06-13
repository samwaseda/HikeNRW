from openai import OpenAI
import os
from datetime import timedelta
from string import Template
import re

from HikeNRW.HikeNRW.bahn import get_all_data, Bahn, get_train_stations
from HikeNRW.HikeNRW.komoot.komoot import get_komoot_dict
from HikeNRW.HikeNRW.komoot.url_parser import extract_komoot_id
from HikeNRW.HikeNRW.tools import round_time, similar
from HikeNRW.HikeNRW.upload_gpx import upload
from HikeNRW.HikeNRW.chatbot import get_message as chatbot_get_message
from HikeNRW.HikeNRW.create_announcement import get_image, export_banner_image


def extract_komoot_url(text):
    matches = re.findall(r'https?://(?:www\.)?komoot[^\s]*', text)
    if len(matches) == 0:
        raise ValueError("No komoot link found")
    return matches[0]


def get_description(bahn_message, komoot_message, tag, comment=None):
    result = {}
    bahn_all_data = get_all_data(bahn_message)
    bahn = Bahn(bahn_all_data).get_results()
    komoot = get_komoot_dict(extract_komoot_id(komoot_message))
    komoot["url"] = extract_komoot_url(komoot_message)
    train_stations_df = get_train_stations(
        komoot["tour"].start_point.lat, komoot["tour"].start_point.lon
    )
    if "name" not in train_stations_df or len(train_stations_df["name"]) == 0:
        result["warning"] = "It looks like there is no train station nearby"
    elif max([similar(nn, bahn_all_data["arr_station"].iloc[-1]) for nn in train_stations_df["name"]]) < 0.7:
        result["warning"] = "It looks like the name of the train station does not match"
    meeting_time = round_time(bahn["starting_time"] - timedelta(minutes=5), 15)
    r_time = bahn["arrival_time"] - bahn["starting_time"] + komoot["total_duration"] + bahn["arrival_time"] + timedelta(hours=1)
    with open("event_description.txt", "r") as f:
        event_description = Template(parse(f.read(), tag))
    gpx_url = upload(
        komoot["tour"].gpx_track.to_xml(),
        bahn["starting_time"].strftime("%Y%m%d") + "_" + komoot["id"]
    )

    try:
        img_url = "INSTAGRAM/" + komoot["id"] + ".jpg"
        get_image(
            komoot_dict=komoot,
            date=meeting_time.strftime("%d %h %A %H:%M"),
            meeting_point=bahn["meeting_point"],
        ).save(img_url)
        result["img"] = img_url
        banner_url = f"INSTAGRAM/banner_{komoot['id']}.jpg"
        export_banner_image(komoot_dict=komoot).save(banner_url)
        result["banner"] = banner_url
    except Exception as e:
        pass

    result["text"] = event_description.substitute(
        tag=f"for {tag}",
        title=komoot["name"],
        date=bahn["starting_time"].strftime("%h %d %Y %A"),
        meeting_time=meeting_time.strftime("%H:%M"),
        meeting_point=bahn["meeting_point"],
        train_schedule=bahn["train_schedule"],
        total_distance=round(komoot["distance"] / 100) / 10,
        elevation_up=round(komoot["elevation_up"]),
        elevation_down=round(komoot["elevation_down"]),
        total_duration=":".join(str(komoot["total_duration"]).split(":")[:-1]),
        return_time=round_time(r_time, 30).strftime("%H:%M"),
        difficulty=komoot["difficulty"],
        gpx_file=gpx_url,
        komoot_link=komoot["url"],
        komoot_frame=komoot["html"],
    )
    if comment is not None:
        result["text"] += comment
    return result


def parse(content, tag):
    content = re.sub(rf"<Not for (?!{tag}\b)[^>]+>\s*", "", content)
    content = re.sub(f"<For {tag}>\s*", "", content)
    pattern = re.compile(r"<[^>]+>")
    content = "\n".join([line for line in content.split("\n")if not pattern.search(line)])
    return content


def get_message(description):
    # Start OpenAI client
    with open("event_assistent.txt", "r") as f:
        assistent = f.read()
    message = [
        {"role": "system", "content": assistent},
        {"role": "user", "content": description}
    ]
    return chatbot_get_message(message)
