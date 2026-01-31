# This example show how to use inline keyboards and process button presses
import telebot
from HikeNRW.HikeNRW.event import get_description
from datetime import datetime, timedelta
from collections import defaultdict

last_communication = datetime.now()
data_dict = defaultdict(dict)

with open("BOT_API", "r") as f:
    TELEGRAM_TOKEN = f.read().split("\n")[0]

bot = telebot.TeleBot(TELEGRAM_TOKEN)


def initialize_data_dict(force=False):
    global last_communication, data_dict
    if datetime.now() - last_communication > timedelta(minutes=15) or force:
        data_dict = defaultdict(dict)
    last_communication = datetime.now()


def send_message(data_dict, bot, message):
    global last_communication
    if "train" in data_dict and "komoot" in data_dict:
        with open("bot.log", "a") as f:
            f.write("Train schedule:\n" + data_dict["train"] + "\n")
            f.write("Komoot:\n" + data_dict["komoot"] + "\n")
        for tag in ["telegram announcement"]:
            bot.send_message(message.chat.id, f"Creating text for {tag}")
            description = get_description(
                data_dict["train"],
                data_dict["komoot"],
                tag=tag,
                comment=data_dict.get("comment", None),
            )
            if "warning" in description:
                bot.send_message(message.chat.id, description["warning"])
            with open("bot.log", "a") as f:
                f.write("Input:\n" + description["text"] + "\n")
            print(description["text"])
            bot.send_message(
                message.chat.id, "You can use the following text for ChatGPT"
            )
            bot.send_message(message.chat.id, description["text"])
        if "img" in description:
            with open(description["img"], "rb") as photo:
                bot.send_photo(message.chat.id, photo)
        if "banner" in description:
            with open(description["banner"], "rb") as photo:
                bot.send_photo(message.chat.id, photo)


@bot.message_handler(commands=["start", "clear"])
def send_welcome(message):
    initialize_data_dict()
    bot.reply_to(message, "Ready to receive data")


@bot.message_handler(regexp="www.bahn.de")
def train_handler_german(message):
    initialize_data_dict()
    data_dict[message.chat.id]["train"] = message.text
    bot.send_message(message.chat.id, "Got a train schedule")
    print(
        "Got a train schedule: ", message.text, " from ", message.from_user.first_name
    )
    send_message(data_dict[message.chat.id], bot, message)


@bot.message_handler(regexp="int.bahn.de")
def train_handler(message):
    initialize_data_dict()
    data_dict[message.chat.id]["train"] = message.text
    bot.send_message(message.chat.id, "Got a train schedule")
    print(
        "Got a train schedule: ", message.text, " from ", message.from_user.first_name
    )
    send_message(data_dict[message.chat.id], bot, message)


@bot.message_handler(regexp=r"\b\d{9,11}\b")
def komoot_hander(message):
    initialize_data_dict()
    data_dict[message.chat.id]["komoot"] = message.text
    bot.send_message(message.chat.id, "Got a Komoot link")
    print("Got a Komoot link: ", message.text, " from ", message.from_user.first_name)
    send_message(data_dict[message.chat.id], bot, message)


@bot.message_handler(func=lambda call: True)
def comment_handler(message):
    initialize_data_dict()
    data_dict[message.chat.id]["comment"] = message.text
    print("Got a message: ", message.text, " from ", message.from_user.first_name)
    bot.send_message(message.chat.id, f"Got a comment: {message.text}")


bot.infinity_polling()
