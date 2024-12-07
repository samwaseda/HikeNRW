import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from collections import defaultdict
from datetime import datetime, timedelta
from openai import OpenAI
import os
from chatbot import get_message

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


all_comments = defaultdict(dict)


@bot.message_handler(commands=["answer"])
def answer(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass
    message = [{
        "role": "system",
        "content": "You are helpful assistant of a hiking group and observes its chatroom"
    }]
    for key, value in all_comments[message.chat.id]:
        if message.reply_to_message.message_id == key:
            message += [value.pop("name")]
            break
        else:
            message += [value]
    else:
        raise ValueError("Message not found")
    text = get_message(message)
    bot.send_message(
        message.chat.id, text, reply_to_message_id=message.reply_to_message.message_id
    )


welcome_message_ids = {}

@bot.message_handler(content_types=["new_chat_members"])
def greet_new_member(message):
    for member in message.new_chat_members:
        if member.is_bot and member.id == bot.get_me().id:
            # The bot has been added to the group
            sent_message = bot.send_message(
                message.chat.id,
                "Don't forget to add me as an admin for you to use all functionalities!",
            )
            # Store the message ID for later deletion
            welcome_message_ids[message.chat.id] = sent_message.message_id


def remove_message(message):
    chat_id = message.chat.id
    if chat_id in welcome_message_ids:
        try:
            bot.delete_message(chat_id, welcome_message_ids[chat_id])
            # Remove the entry from the dictionary
            del welcome_message_ids[chat_id]
        except Exception as e:
            print(f"Failed to delete message: {e}")


@bot.message_handler(
    func=lambda msg: msg.content_type == 'text' and not msg.text.startswith('/')
)
def comment_handler(message):
    remove_message(message)
    user_name = message.from_user.first_name
    is_admin = bot.get_chat_member(
        message.chat.id, message.from_user.id
    ).status in ['administrator', 'creator']
    is_myself = message.from_user.id == bot.get_me().id
    if is_myself:
        role = "assistant"
    else:
        role = "user"
    text = message.text
    if is_admin:
        user_name = user_name + " (admin)"
    elif len(text) > 100:
        text = text[:100] + "..."
    message_id = message.message_id
    all_comments[message.chat.id][message_id] = {
        "role": role, "name": user_name, "text": text
    }


bot.infinity_polling()
