# This example show how to use inline keyboards and process button presses
import telebot
from HikeNRW.HikeNRW.event import get_description, get_message
from datetime import datetime, timedelta


data_dict = {}
last_communication = datetime.now()

with open("BOT_API", "r") as f:
    TELEGRAM_TOKEN = f.read().split("\n")[0]

bot = telebot.TeleBot(TELEGRAM_TOKEN)


def check_last_communication():
    global last_communication, data_dict
    if datetime.now() - last_communication > timedelta(minutes=15):
        data_dict = {}
    last_communication = datetime.now()


def send_message(data_dict, bot, message):
    if "train" in data_dict and "komoot" in data_dict:
        for tag in ["html", "telegram announcement", "telegram group", "Facebook event"]:
            try:
                bot.send_message(message.chat.id, f"Creating text for {tag}")
                description = get_description(
                    data_dict["train"],
                    data_dict["komoot"],
                    tag=tag,
                    comment=data_dict.get("comment", None)
                )
                if "warning" in description:
                    bot.send_message(message.chat.id, description["warning"])
                m = get_message(description["text"])
                print(m)
                bot.send_message(message.chat.id, m)
            except Exception as e:
                bot.send_message(message.chat.id, str(e))


@bot.message_handler(regexp="int.bahn.de")
def train_handler(message):
    check_last_communication()
    data_dict["train"] = message.text
    bot.send_message(message.chat.id, "Got a train schedule")
    send_message(data_dict, bot, message)


@bot.message_handler(regexp=r'\b\d{9,11}\b')
def komoot_hander(message):
    check_last_communication()
    data_dict["komoot"] = message.text
    bot.send_message(message.chat.id, "Got a Komoot link")
    send_message(data_dict, bot, message)


@bot.message_handler(func=lambda call: True)
def comment_handler(message):
    check_last_communication()
    data_dict["comment"] = message.text
    bot.send_message(message.chat.id, f"Got a comment: {message.text}")


bot.infinity_polling()
