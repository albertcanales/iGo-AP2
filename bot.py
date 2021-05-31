from telegram import ParseMode, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from igo import *

igraph = None # The iGraph used by the bot
locations = {} # Contains the location for each user

def start(update, context):
    '''
    Command /start. General description of the bot.
    Params:
        - update: Telegram's update
        - context: Telegram's context
    This funcion does not return anything.
    '''
    message = "I am *iGo*. I can guide you through Barcelona, my _amigo_ 🚗!\n Type /help to see what I can do for you"
    send_message(update, context, message)

def help(update, context):
    '''
    Command /help. Lists available commands for the bot.
    Params:
        - update: Telegram's update
        - context: Telegram's context
    This funcion does not return anything.
    '''
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
    '''
    Command /author. Displays the authors of the project.
    Params:
        - update: Telegram's update
        - context: Telegram's context
    This funcion does not return anything.
    '''
    message = '''
My almighty creators are:
- Javier Nistal Salas
- Albert Canales Ros
'''
    send_message(update, context, message)


def go(update, context):
    '''
    Command /go. Finds and displays the path to the location implied in the message.
    Params:
        - update: Telegram's update
        - context: Telegram's context
    This funcion does not return anything.
    '''
    text = get_command_parameters(update)
    if text is not None:
        target = igraph.get_location(text)
        if target is not None:
            if get_chat_id(update) in locations.keys():
                filename = "%s.png" % get_chat_id(update)
                path = igraph.get_shortest_path(locations[get_chat_id(update)], target, filename)
                if path is not None:
                    print("Path from %s to %s" %(str(path[0]), str(path[-1])))
                    send_map(update, context, filename)
                    os.remove(filename)
                else:
                    send_message(update, context, "⛔ There is no possible path between the two locations! ⛔")
            else:
                send_message(update, context, "🚫 I don't have your location 📍. Send it so I can guide you!")
        else:
            send_location_error(update, context)

def where(update, context):
    '''
    Command /where. Displays the stored location of the user.
    Params:
        - update: Telegram's update
        - context: Telegram's context
    This funcion does not return anything.
    '''
    if get_chat_id(update) in locations.keys():
        print("Location to show:", locations[get_chat_id(update)])
        send_map(update, context, locations[get_chat_id(update)])
        send_message(update, context, "ℹ️ Send me your actual location 📍 if you want to change it")
    else:
        print("No location to show")
        send_message(update, context, "🚫 I don't have your location 📍. Send it to me!")
    

def pos(update, context):
    '''
    Secret command /pos. Updates the global location with the given one.
    Params:
        - update: Telegram's update
        - context: Telegram's context
    This funcion does not return anything.
    '''
    send_message(update, context, "How do you know about this, are you a hacker? Please don't hurt me 😨!")
    text = get_command_parameters(update)
    if text is not None:
        loc = igraph.get_location(text)
        if loc is not None:
            global locations
            locations[get_chat_id(update)] = loc
            send_message(update, context, "🔄 Got it! Your location has been *updated*")
            print("Manual location:", loc)
        else:
            send_location_error(update, context)



def set_location(update, context):
    '''
    Given a location message, it updates it to locations.
    Params:
        - update: Telegram's update
        - context: Telegram's context
    This funcion does not return anything.
    '''
    global locations
    locations[get_chat_id(update)] = Location(update.message.location.longitude, update.message.location.latitude)
    send_message(update, context, "🔄 I've *updated* your location!\nIf only I had legs to move as well...")
    print("Given location:", locations[get_chat_id(update)])

def send_message(update, context, message):
    '''
    Sends message formatted as Markdown.
    Params:
        - update: Telegram's update
        - context: Telegram's context
        - message: string with the message that should be sent with markdown format.
    This funcion does not return anything.
    '''
    context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.MARKDOWN)

def send_location_error(update, context):
    '''
    Informs the user that the given location is not valid.
    Params:
        - update: Telegram's update
        - context: Telegram's context
    This funcion does not return anything.
    '''
    send_message(update, context, "🚫 Your location is *not valid*, give me the coordinates or a name")

def send_map(update, context, filename):
    '''
    Sends a map given a Location or a path (list of Locations).
    Params:
        - update: Telegram's update
        - context: Telegram's context
        - filename: A string with the name of the image.
    This funcion does not return anything.
    '''
    try:
        context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=open(filename, 'rb'))
    except Exception as e:
            print(e)
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='💣')

def get_chat_id(update):
    '''
    Auxiliary function to get chat id
    Params:
        - update: Telegram's update
    Returns the obtained chat id.
    '''
    return update.message.chat.id

def get_command_parameters(update):
    '''
    Separates the command from the parameters if possible.
    Params:
        - update: Telegram's update
    Returns the additional text, None if there is none.
    '''
    splitted_com = update.message.text.split(None, 1) # Separates between the first word
    if len(splitted_com) > 1:
        return splitted_com[1]
    else:
        send_location_error(update, context)
        return None


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
