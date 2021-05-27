from telegram import ParseMode, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from igo import Location, get_location

location = None

def send_message(update, context, message):
    '''Auxiliary function to simplify calls'''
    context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.MARKDOWN)

def set_location(update, context):
    '''Given a location message, it updates the global location variable'''
    global location
    location = Location(update.message.location.latitude, update.message.location.longitude)
    send_message(update, context, "I've updated your location! If only I had legs to move as well...")
    print(location)
    

def start(update, context):
    '''Command /start. General description of the bot'''
    message = "I am *iGo* 🤖️ and I can take you wherever you want from Barcelona! Type /help to see what I can do for you"
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
My creators are:
- Javier Nistal Salas
- Albert Canales Ros
'''
    send_message(update, context, message)


def go(update, context):
    pass

def where(update, context):
    global location
    print(location)
    if location is not None:
        try:
            fitxer = "%d.png" % random.randint(1000000, 9999999)
            mapa = StaticMap(500, 500)
            mapa.add_marker(CircleMarker(location, 'blue', 10))
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
        send_message(update, context, "Send me your actual location if you want to change it")
    else:
        send_message(update, context, "I don't have your location 😔. Send it so I can guide you!")
    

def pos(update, context):
    '''Secret command /pos. Updates the global location with the given one'''
    message = "How do you know about this, are you a hacker? Please don't hurt me!\n"
    loc = get_location(update.message.text)
    if loc is not None:
        global location
        location = loc
        message += "Got it! Your location has been *updated*"
    else:
        message += "Your location is *not valid*, give me the coordinates or a name"
    send_message(update, context, message)

def main():
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

main()
