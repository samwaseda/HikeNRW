import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from collections import defaultdict
from datetime import datetime

with open("BOT_API", "r") as f:
    TELEGRAM_TOKEN = f.read().split("\n")[0]

bot = telebot.TeleBot(TELEGRAM_TOKEN)


class State:
    state = defaultdict(list)

    def update_state(self, chat_id, group_id, key):
        self.state[f"{chat_id}_{group_id}"].append(key)

    def get_key(self, chat_id, group_id):
        questions = get_all_questions()
        for key in questions.keys():
            if key not in self.state[f"{chat_id}_{group_id}"]:
                return key
        return None


def get_all_questions():
    return {
        "overall": {
            "Question": "How was the event overall?",
            "Answers": ["Very good!", "Good", "ok", "Bad", "Very bad"]
        },
        "length": {
            "Question": "How was the length?",
            "Answers": [
                "Too long",
                "Somewhat long",
                "Good length",
                "Somewhat short",
                "Too short"
            ]
        },
        "elevation": {
            "Question": "How was the elevation?",
            "Answers": [
                "Too hilly",
                "Somewhat hilly",
                "Good elevation",
                "Somewhat flat",
                "Too flat"
            ]
        },
        "train": {
            "Question": "How was the train ride?",
            "Answers": ["Too long", "Somewhat long", "Reasonable"]
        }
    }


@bot.message_handler(commands=["feedback"])
def create_feedback(message):
    link = hex(message.chat.id)[2:]
    bot.send_message(
        message.chat.id,
        (
            "Thanks for joining today's hike! We hope you all enjoyed it!\n"
            "We would love to hear from you what you think of today's hike, so"
            " if you have time click on the link below to give us your"
            " feedback! It is fully anonymous! The link is valid for around"
            " 24 hours.\n\n"
            f"https://t.me/HikeNRWBot?start=review{link}"
        )
    )


@bot.message_handler(commands=["start"], regexp="start review")
def get_review(message):
    group_id = message.text.split("review")[-1]
    questions = get_all_questions()
    for key, content in questions.items():
        if key not in state[message.chat.id + group_id]:
            bot.send_message(
                message.chat.id,
                content["Question"],
                reply_markup=gen_markup(
                    f"{key}_{message.chat.id}_{group_id}", content["Answers"]
                )
            )
            break


def gen_markup(key, choices):
    markup = InlineKeyboardMarkup()
    markup.add(*[
        InlineKeyboardButton(choice, callback_data=key + "_" + choice)
        for choice in choices
    ])
    return markup


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    key, chat_id, group_id, content = call.data.split("_")
    state.update_state(chat_id, group_id, key)
    print(key, content)
    questions = get_all_questions()
    item = state.get_key(chat_id, group_id)
    if item is None:
        bot.send_message(
            int(chat_id),
            "If you have further feedback, please write it here! Thanks for your time!"
        )
        return
    bot.send_message(
        chat_id,
        questions[item]["Question"],
        reply_markup=gen_markup(f"{key}_{chat_id}", questions[item]["Answers"])
    )

# @bot.message_handler(func=lambda message: True)
# def message_handler(message):
#     bot.send_message(message.chat.id, "Yes/no?", reply_markup=gen_markup())

bot.infinity_polling()
