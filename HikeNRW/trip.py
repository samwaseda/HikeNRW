import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import os
import yaml
import math

with open("TRIPBOT_API", "r") as f:
    TELEGRAM_TOKEN = f.read().split("\n")[0]

bot = telebot.TeleBot(TELEGRAM_TOKEN)

with open("data/trips.yml", "r") as f:
    all_trips = yaml.safe_load(f)


def haversine(lat2, lon2):
    # Düsseldorf central station coordinates
    lat1 = 51.2201
    lon1 = 6.7927
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    # Radius of Earth (in kilometers)
    R = 6371.0
    distance = R * c
    return distance


def calculate_bearing(lat2, lon2):
    """
    Calculate the initial bearing (in degrees) between two coordinates.
    """
    # Düsseldorf central station coordinates
    lat1 = 51.2201
    lon1 = 6.7927
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Calculate the difference in longitude
    dlon = lon2 - lon1
    
    # Calculate the bearing
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    bearing = math.atan2(x, y)
    
    # Convert from radians to degrees and normalize to 0-360°
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360  # Normalize to 0-360
    return bearing


def bearing_to_compass(bearing):
    """
    Convert a bearing (in degrees) to a compass direction (e.g., N, NE, E, etc.).
    """
    compass_directions = [
        "North", "North-East", "East", "South-East",
        "South", "South-West", "West", "North-West"
    ]
    # Divide the circle into 16 sectors of 22.5° each
    sector_size = 360 / len(compass_directions)
    index = int((bearing + sector_size / 2) // sector_size) % len(compass_directions)
    return compass_directions[index]


def get_trip_by_name(trip_name):
    for t in all_trips["trips"]:
        if t["name"] == trip_name:
            return t
    return None


@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    bot.reply_to(
        message,
        "Welcome to the Trip Bot! Use /trip to see upcoming trips and their details."
    )


@bot.message_handler(commands=["trip"])
def show_trips(message):
    print(f"User {message.from_user.username} requested trip info.")
    # Return the content of trips.yml as a preview
    trip_dict = {}
    for t in all_trips["trips"]:
        start = datetime.strptime(t["dates"]["start"], "%Y-%m-%d")
        end = datetime.strptime(t["dates"]["end"], "%Y-%m-%d")
        if end < datetime.now():
            continue
        trip_dict[t["name"]] = f"{start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}\n{t['name']}"
    # Show the trips as inline buttons
    markup = InlineKeyboardMarkup()
    for trip_name, trip_info in trip_dict.items():
        markup.add(InlineKeyboardButton(trip_info, callback_data=trip_name))    
    bot.send_message(message.chat.id, "Select a trip to see details:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def trip_details(call):
    print(f"User {call.from_user.username} requested details for trip {call.data}.")
    trip = get_trip_by_name(call.data)
    if trip is None:
        bot.answer_callback_query(call.id, "Trip not found.")
        return
    start = datetime.strptime(trip["dates"]["start"], "%Y-%m-%d")
    end = datetime.strptime(trip["dates"]["end"], "%Y-%m-%d")
    details = f"*{trip['name']}*\n\n"
    n_nights = (end - start).days
    details += f"Dates: {start.strftime('%A, %B %d, %Y')} - {end.strftime('%A, %B %d, %Y')} ({n_nights} nights)\n\n"
    details += f"Destination: {trip['destination']}\n\n"
    if "coordinates" in trip:
        distance = haversine(trip["coordinates"][0], trip["coordinates"][1])
        compass_dir = bearing_to_compass(calculate_bearing(trip["coordinates"][0], trip["coordinates"][1]))
        details += f"Distance from Düsseldorf: {distance:.1f} km ({compass_dir})\n\n"
    details += f"URL: {trip['url']}\n\n"
    details += f"Current list of participants: {', '.join(sorted(trip['participants']))}\n\n"
    details += f"Number of spots available: {trip['max_participants'] - len(trip['participants'])}\n\n"
    c_pp = trip['total_costs'] / trip['max_participants']
    details += f"Total cost: {trip['total_costs']} € = {c_pp:.2f} € pp if fully booked\n"
    if "description" in trip:
        details += f"{trip['description']}\n\n"
    if "itinerary" in trip:
        details += "Itinerary:\n"
        for day in trip["itinerary"]:
            day_date = start + timedelta(days=day["day"] - 1)
            details += f"**Day {day['day']} - {day_date.strftime('%B %d, %Y')}**: {day['activities']}\n"
    for note in trip.get("notes", []):
        details += f"\n_{note}_\n"
    details += "\nTo see more trips, use /trip."
    bot.send_message(call.message.chat.id, details, parse_mode='Markdown')


# Forward every message given by any user to @samwaseda (or user id: 1545807495)
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.forward_message(all_trips["sams_id"], message.chat.id, message.message_id)



bot.infinity_polling()
