from openai import OpenAI
import os
from datetime import timedelta

from HikeNRW.HikeNRW.bahn import get_all_data, Bahn
from HikeNRW.HikeNRW.komoot.komoot import get_komoot_dict
from HikeNRW.HikeNRW.komoot.url_parser import extract_komoot_id
from HikeNRW.HikeNRW.tools import round_time


def get_description(bahn_message, komoot_message):
    bahn = Bahn(get_all_data(bahn_message)).get_results()
    komoot = get_komoot_dict(extract_komoot_id(komoot_message))
    meeting_time = round_time(bahn["starting_time"] - timedelta(minutes=5), 15)
    r_time = bahn["arrival_time"] - bahn["starting_time"] + komoot["total_duration"] + bahn["arrival_time"] + timedelta(hours=1)

    items = [
        "Write a casual entertaining hiking event description (Do not change the format of the train schedule) in HTML with:"
        "Title: {} (needless to put it explicitly in the text)".format(komoot["name"].replace("2024/07/07", "Hiking")),
        "Date: {}".format(bahn["starting_time"].strftime("%h %d %Y")),
        "We see each other at {} at {} but they are free to join wherever they want".format(
            meeting_time.strftime("%H:%M"), bahn["meeting_point"]
        ),
        "Train schedule:\n{}".format(bahn["train_schedule"]),
        "Total distance: {} km".format(round(komoot["distance"] / 100) / 10),
        "Elevation up: {} m & down: {} m".format(round(komoot["elevation_up"]), round(komoot["elevation_down"])),
        "Total duration according to Komoot: {}".format(":".join(str(komoot["total_duration"]).split(":")[:-1])),
        "We will be back at {} around {} (with considerable uncertainty)".format(
            bahn["meeting_point"],
            round_time(r_time, 30).strftime("%H:%M"),
        ),
        "Level: {} (according to Komoot)".format(komoot["difficulty"]),
        "Komoot link: {}".format(komoot["url"]),
        # "Komoot frame: {}".format(komoot["html"]),
        "Regardless of the weather, I will NOT cancel the event.",
    ]
    return "\n\n".join(items)


def get_message(description):
    api_key = os.environ["GWDG_LLM_KEY"]
    base_url = "https://chat-ai.academiccloud.de/v1"
    model = "meta-llama-3-70b-instruct"
    # Start OpenAI client
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    with open("markdown.txt", "r") as f:
        markdown = f.read()
    chat_completion = client.chat.completions.create(
            messages=[
                {"role":"system", "content": "You are a helpful assistant"},
                {"role": "assistent", "content": markdown},
                {
                    "role":"user", "content": description
                }],
            model=model,
        )
    return chat_completion.choices[0].message.content
