# This example show how to use inline keyboards and process button presses
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from HikeNRW.HikeNRW.event import get_description, get_message


data_dict = {}

with open("BOT_API", "r") as f:
    TELEGRAM_TOKEN = f.read().split("\n")[0]

bot = telebot.TeleBot(TELEGRAM_TOKEN)


def get_event_message(data):
    description = get_description(data["train"], data["komoot"])
    return get_message(description)

@bot.message_handler(regexp="int.bahn.de")
def message_handler(message):
    data_dict["train"] = message.text
    bot.send_message(message.chat.id, "Got a train schedule")
    if "train" in data_dict and "komoot" in data_dict:
        bot.send_message(message.chat.id, "Creating message")
        m = get_event_message(data_dict)
        print(m)
        bot.send_message(message.chat.id, m, parse_mode="HTML")

@bot.message_handler(regexp=r'\b\d{9,11}\b')
def message_handler(message):
    data_dict["komoot"] = message.text
    bot.send_message(message.chat.id, "Got a Komoot link")
    if "train" in data_dict and "komoot" in data_dict:
        bot.send_message(message.chat.id, "Creating message")
        m = get_event_message(data_dict)
        print(m)
        bot.send_message(message.chat.id, m, parse_mode="HTML")


bot.infinity_polling()
