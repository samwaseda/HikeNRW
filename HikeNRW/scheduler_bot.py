# This example show how to use inline keyboards and process button presses
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from HikeNRW.HikeNRW.event import get_description, get_message


data_dict = {}

with open("BOT_API", "r") as f:
    TELEGRAM_TOKEN = f.read().split("\n")[0]

bot = telebot.TeleBot(TELEGRAM_TOKEN)


def get_event_message(data, appearance=""):
    description = get_description(data["train"], data["komoot"], appearance=appearance)
    return get_message(description)


def send_message(data_dict, bot, message):
    if "train" in data_dict and "komoot" in data_dict:
        bot.send_message(message.chat.id, "Creating message")
        for appearance in ["", "in HTML"]:
            try:
                m = get_event_message(data_dict, appearance=appearance)
                print(m)
                if "warning" in result:
                    bot.send_message(message.chat.id, m["warning"])
                bot.send_message(message.chat.id, m["text"])
            except Exception as e:
                bot.send_message(message.chat.id, str(e))


@bot.message_handler(regexp="int.bahn.de")
def message_handler(message):
    data_dict["train"] = message.text
    bot.send_message(message.chat.id, "Got a train schedule")
    send_message(data_dict, bot, message)


@bot.message_handler(regexp=r'\b\d{9,11}\b')
def message_handler(message):
    data_dict["komoot"] = message.text
    bot.send_message(message.chat.id, "Got a Komoot link")
    send_message(data_dict, bot, message)


bot.infinity_polling()
