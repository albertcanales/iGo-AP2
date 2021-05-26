from telegram import ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

def send_message(context, update, message):
    context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.MARKDOWN)

def start(update, context):
    message = '''I am *iGo* 🤖️ and I can take you wherever you want from Barcelona! Type /help to see what I can do for you'''
    send_message(context, update, message)

def help(update, context):
    message = '''
    Hi! Here's what I am capable of:
- /start: I will guide you to get to your destination
- /help: I will show available commands (recursion, yay!)
- /author: I will show you my creators
- /go `place`: Tell me a `place` from Barcelona (name or coordinates) and I will show you the optimal path.
- /where: I will show your actual position.
    '''
    send_message(context, update, message)



def author(update, context):
    message = '''My creators are:
- Javier Nistal Salas
- Albert Canales Ros'''
    send_message(context, update, message)


def go(update, context):
    pass

def where(update, context):
    try:
        lat, lon = update.message.location.latitude, update.message.location.longitude
        print(lat, lon)
        fitxer = "%d.png" % random.randint(1000000, 9999999)
        mapa = StaticMap(500, 500)
        mapa.add_marker(CircleMarker((lon, lat), 'blue', 10))
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

def pos(update, context):
    message = "How do you know about this, are you a hacker? Please don't hurt me!\n"
    # TODO Pillar la posició
    message += "Anyways, *your location has been updated*"
    send_message(context, update, message)



TOKEN = open('token.txt').read().strip()
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('help', help))
dispatcher.add_handler(CommandHandler('author', author))
dispatcher.add_handler(CommandHandler('go', go))
dispatcher.add_handler(CommandHandler('pos', pos))
dispatcher.add_handler(MessageHandler(Filters.location, where))
updater.start_polling()