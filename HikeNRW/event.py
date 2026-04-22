from datetime import timedelta
from pathlib import Path
from string import Template

from HikeNRW.HikeNRW.bahn import get_all_data, Bahn, get_train_stations
from HikeNRW.HikeNRW.komoot import get_komoot_dict
from HikeNRW.HikeNRW.tools import round_time, similar
from HikeNRW.HikeNRW.upload_gpx import upload
from HikeNRW.HikeNRW.create_announcement import get_image, export_banner_image


def get_description(bahn_message, komoot_message, comment=None):
    result = {}
    bahn_all_data = get_all_data(bahn_message)
    bahn = Bahn(bahn_all_data).get_results()
    komoot = get_komoot_dict(komoot_message)
    try:
        train_stations_df = get_train_stations(
            komoot["tour"].start_point.lat, komoot["tour"].start_point.lon
        )
        if "name" not in train_stations_df or len(train_stations_df["name"]) == 0:
            result["warning"] = "It looks like there is no train station nearby"
        elif (
            max(
                [
                    similar(nn, bahn_all_data["arr_station"].iloc[-1])
                    for nn in train_stations_df["name"]
                ]
            )
            < 0.7
        ):
            result["warning"] = "It looks like the name of the train station does not match"
    except:
        result["warning"] = "Failed to check train station, maybe there is no station nearby"
    meeting_time = round_time(bahn["starting_time"] - timedelta(minutes=5), 15)
    r_time = (
        bahn["arrival_time"]
        - bahn["starting_time"]
        + komoot["total_duration"]
        + bahn["arrival_time"]
        + timedelta(hours=1)
    )
    with open(Path(__file__).with_name("event_description.txt"), "r") as f:
        event_description = Template(f.read())
    gpx_url = upload(
        komoot["tour"].gpx_track.to_xml(),
        bahn["starting_time"].strftime("%Y%m%d") + "_" + komoot["id"],
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
        print("Could not create image:", e)
        pass

    result["text"] = event_description.substitute(
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
    )
    if comment is not None:
        result["text"] += comment
    return result
