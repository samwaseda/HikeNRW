# This example show how to use inline keyboards and process button presses
import telebot
from HikeNRW.HikeNRW.event import get_description, get_message


data_dict = {}

with open("BOT_API", "r") as f:
    TELEGRAM_TOKEN = f.read().split("\n")[0]

bot = telebot.TeleBot(TELEGRAM_TOKEN)


def send_message(data_dict, bot, message):
    if "train" in data_dict and "komoot" in data_dict:
        bot.send_message(message.chat.id, "Creating message")
        for appearance in ["", "in HTML"]:
            try:
                description = get_description(
                    data_dict["train"], data_dict["komoot"], appearance=appearance
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
    data_dict["train"] = message.text
    bot.send_message(message.chat.id, "Got a train schedule")
    send_message(data_dict, bot, message)


@bot.message_handler(regexp=r'\b\d{9,11}\b')
def komoot_hander(message):
    data_dict["komoot"] = message.text
    bot.send_message(message.chat.id, "Got a Komoot link")
    send_message(data_dict, bot, message)


bot.infinity_polling()
