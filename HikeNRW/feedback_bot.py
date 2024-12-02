import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from collections import defaultdict
from datetime import datetime, timedelta

with open("FEEDBACK_BOT_API", "r") as f:
    TELEGRAM_TOKEN = f.read().split("\n")[0]

bot = telebot.TeleBot(TELEGRAM_TOKEN)


state = defaultdict(list)
message_to_delete = defaultdict(list)
poll_created = {}
group_name = {}
user_feedback = defaultdict(dict)


def update_state(state, chat_id, group_id, key):
    state[f"{chat_id}_{group_id}"].append(key)


def get_key(state, chat_id, group_id):
    questions = get_all_questions()
    for key in questions.keys():
        if key not in state[f"{chat_id}_{group_id}"]:
            return key
    return None


def get_all_questions():
    return {
        "overall": {
            "Question": "How was the event overall?",
            "Answers": ["Very good!", "Good", "ok", "Bad", "Very bad"],
        },
        "length": {
            "Question": "How was the length?",
            "Answers": [
                "Too long",
                "Somewhat long",
                "Good length",
                "Somewhat short",
                "Too short",
            ],
        },
        "elevation": {
            "Question": "How was the elevation?",
            "Answers": [
                "Too hilly",
                "Somewhat hilly",
                "Good elevation",
                "Somewhat flat",
                "Too flat",
            ],
        },
        "train": {
            "Question": "How was (the length of) the train/bus ride?",
            "Answers": ["Too long", "Somewhat long", "Reasonable"],
        },
    }


def get_group_name(message):
    try:
        return bot.get_chat(message.chat.id).title
    except telebot.apihelper.ApiException as e:
        bot.reply_to(message, f"Failed to retrieve group name: {e}")


@bot.message_handler(commands=["feedback"])
def create_feedback(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass
    link = hex(message.chat.id)[2:]
    status = bot.get_chat_member(message.chat.id, message.from_user.id).status
    if status not in ['administrator', 'creator']:
        bot.send_message(
            message.chat.id,
            "Sorry, only the organizer can create a feedback link!",
        )
        return
    bot.send_message(
        message.chat.id,
        (
            "Thanks for joining today's hike! We hope you all enjoyed it!\n"
            "We would love to hear from you what you think of today's hike, so"
            " if you have time click on the link below to give us your"
            " feedback! It is fully anonymous! The link is valid for"
            " 48 hours.\n\n"
            f"https://t.me/hikenrwchatbot?start=review{link}"
        ),
    )
    poll_created[link] = datetime.now()
    group_name[link] = get_group_name(message)


@bot.message_handler(commands=["start"], regexp="start review")
def get_review(message):
    group_id = message.text.split("review")[-1]
    if group_id not in poll_created:
        return
    bot.delete_message(message.chat.id, message.message_id)
    get_reaction(state, message.chat.id, group_id)


def gen_markup(key, choices):
    markup = InlineKeyboardMarkup()
    markup.add(
        *[
            InlineKeyboardButton(choice, callback_data=key + "_" + choice)
            for choice in choices
        ]
    )
    return markup


def get_reaction(state, chat_id, group_id):
    questions = get_all_questions()
    item = get_key(state, chat_id, group_id)
    if datetime.now() - poll_created[group_id] > timedelta(days=2) or group_id not in poll_created:
        bot.send_message(
            int(chat_id),
            (
                "It looks like the feedback link has expired. Please contact"
                " the organizer if you have any feedback! Thanks!"
            ),
        )
    if item is None:
        bot.send_message(
            int(chat_id),
            (
                "Here's a summary of your feedback:\n\n"
                f"Group: {group_name[group_id]}\n"
                f"Overall: {user_feedback[f'{chat_id}_{group_id}']['overall']}\n"
                f"Length: {user_feedback[f'{chat_id}_{group_id}']['length']}\n"
                f"Elevation: {user_feedback[f'{chat_id}_{group_id}']['elevation']}\n"
                f"Train/Bus: {user_feedback[f'{chat_id}_{group_id}']['train']}\n\n"
                "Thank you for your feedback! We hope to see you again soon!\n\n"
                "If you would like to give more feedback, please simply leave"
                " comments here!"
            ),
        )
        for msg in message_to_delete[int(chat_id)]:
            bot.delete_message(chat_id, msg)
        message_to_delete[int(chat_id)] = []
        return
    message = bot.send_message(
        chat_id,
        questions[item]["Question"],
        reply_markup=gen_markup(
            f"{item}_{chat_id}_{group_id}", questions[item]["Answers"]
        ),
    )
    message_to_delete[int(chat_id)].append(message.message_id)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    key, chat_id, group_id, content = call.data.split("_")
    update_state(state, chat_id, group_id, key)
    user_feedback[f"{chat_id}_{group_id}"][key] = content
    print(key, content)
    get_reaction(state, chat_id, group_id)


bot.infinity_polling()
