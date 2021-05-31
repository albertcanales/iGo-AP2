from telegram import ParseMode, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from staticmap import StaticMap, CircleMarker, Line
from igo import *

igraph = None # The iGraph used by the bot
locations = {} # Contains the location for each user

def start(update, context):
    '''Command /start. General description of the bot'''
    message = "I am *iGo*. I can guide you through Barcelona, my _amigo_ 🚗!\n Type /help to see what I can do for you"
    send_message(update, context, message)

def help(update, context):
    '''Command /help. Lists available commands for the bot'''
    message = '''
Hi! Here's what I am capable of:
- /start: I will guide you to get to your destination
- /help: I will show available commands (recursion, yay!)
- /author: I will show you my creators
- /go `place`: Tell me a `place` from Barcelona (name or coordinates) and I will show you the optimal path.
- /where: I will show your actual position
'''
    send_message(update, context, message)


def author(update, context):
    '''Command /author. Displays the authors of the project'''
    message = '''
My almighty creators are:
- Javier Nistal Salas
- Albert Canales Ros
'''
    send_message(update, context, message)


def go(update, context):
    text = update.message.text.split(None, 1)[1] # Removes the first word
    target = igraph.get_location(text)
    if target is not None:
        if get_user(update) in locations.keys():
            path = igraph.get_shortest_path(locations[get_user(update)], target)
            if path is not None:
                print("Path from %s to %s" %(str(path[0]), str(path[-1])))
                send_map(update, context, path)
            else:
                send_message(update, context, "⛔ There is no possible path between the two locations! ⛔")
        else:
            send_message(update, context, "🚫 I don't have your location 📍. Send it so I can guide you!")
    else:
        send_location_error(update, context)

def where(update, context):
    if get_user(update) in locations.keys():
        print("Location to show:", locations[get_user(update)])
        send_map(update, context, locations[get_user(update)])
        send_message(update, context, "ℹ️ Send me your actual location 📍 if you want to change it")
    else:
        print("No location to show")
        send_message(update, context, "🚫 I don't have your location 📍. Send it to me!")
    

def pos(update, context):
    '''Secret command /pos. Updates the global location with the given one'''
    send_message(update, context, "How do you know about this, are you a hacker? Please don't hurt me 😨!")
    splitted_com = update.message.text.split(None, 1) # Separates between the first word
    if len(splitted_com) > 1:
        text = splitted_com[1]
        loc = igraph.get_location(text)
        if loc is not None:
            global locations
            locations[get_user(update)] = loc
            send_message(update, context, "🔄 Got it! Your location has been *updated*")
            print("Manual location:", loc)
        else:
            send_location_error(update, context)
    else:
        send_location_error(update, context)



def set_location(update, context):
    '''Given a location message, it updates it to locations'''
    global locations
    locations[get_user(update)] = Location(update.message.location.longitude, update.message.location.latitude)
    send_message(update, context, "🔄 I've *updated* your location!\nIf only I had legs to move as well...")
    print("Given location:", locations[get_user(update)])

def send_message(update, context, message):
    '''Auxiliary function to simplify calls'''
    context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.MARKDOWN)

def send_location_error(update, context):
    send_message(update, context, "🚫 Your location is *not valid*, give me the coordinates or a name")

def send_map(update, context, path):
    ''' Sends a map given a Location or a path (list of Locations)'''
    try:
        fitxer = "%s.png" % get_user(update)
        mapa = StaticMap(1000, 1000)
        if isinstance(path, Location):
            mapa.add_marker(CircleMarker(locations[get_user(update)], 'red', 10))
        else:
            mapa.add_marker(CircleMarker(path[0], 'blue', 10))
            mapa.add_line(Line(path, 'blue', 3, False))
            mapa.add_marker(CircleMarker(path[-1], 'red', 10))
        imatge = mapa.render()
        imatge.save(fitxer)
        context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=open(fitxer, 'rb'))
        os.remove(fitxer)
    except Exception as e:
            print(e)
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='💣')

def get_user(update):
    '''Auxiliary function to get username'''
    return update.message.chat.username

def main():

    global igraph
    igraph = iGraph() 

    print("Starting bot...")

    TOKEN = open('token.txt').read().strip()
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', help))
    dispatcher.add_handler(CommandHandler('author', author))
    dispatcher.add_handler(CommandHandler('go', go))
    dispatcher.add_handler(CommandHandler('pos', pos))
    dispatcher.add_handler(CommandHandler('where', where))
    dispatcher.add_handler(MessageHandler(Filters.location, set_location))
    updater.start_polling()

    print("Bot started")

main()
