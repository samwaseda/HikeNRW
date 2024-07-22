from openai import OpenAI
import os
from datetime import timedelta
from string import Template

from HikeNRW.HikeNRW.bahn import get_all_data, Bahn, get_train_stations
from HikeNRW.HikeNRW.komoot.komoot import get_komoot_dict
from HikeNRW.HikeNRW.komoot.url_parser import extract_komoot_id
from HikeNRW.HikeNRW.tools import round_time


def get_description(bahn_message, komoot_message):
    bahn = Bahn(get_all_data(bahn_message)).get_results()
    komoot = get_komoot_dict(extract_komoot_id(komoot_message))
    meeting_time = round_time(bahn["starting_time"] - timedelta(minutes=5), 15)
    r_time = bahn["arrival_time"] - bahn["starting_time"] + komoot["total_duration"] + bahn["arrival_time"] + timedelta(hours=1)
    with open("event_description.txt", "r") as f:
        event_description = Template(f.read())

    return event_description.subsitute(
        title=komoot["name"],
        date=bahn["starting_time"].strftime("%h %d %Y"),
        meeting_time=meeting_time.strftime("%H:%M"),
        meeting_point=bahn["meeting_point"],
        train_schedule=bahn["train_schedule"],
        total_distance=round(komoot["distance"] / 100) / 10,
        elevation_up=round(komoot["elevation_up"]),
        elevation_down=round(komoot["elevation_down"]),
        total_duration=":".join(str(komoot["total_duration"]).split(":")[:-1]),
        return_time=round_time(r_time, 30).strftime("%H:%M"),
        difficulty=komoot["difficulty"],
        komoot_link=komoot["url"],
        komoot_frame=komoot["html"],
    )


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
