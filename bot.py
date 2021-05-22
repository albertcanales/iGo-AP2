from telegram.ext import Updater, CommandHandler

def start(update, context):
    print(update)
    print(context)
    botname = context.bot.username
    username = update.effective_chat.username
    fullname = update.effective_chat.first_name + ' ' + update.effective_chat.last_name
    missatge = "Tu ets en %s (%s) i jo soc el %s." % (fullname, username, botname)
    context.bot.send_message(chat_id=update.effective_chat.id, text=missatge)

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



TOKEN = open('token.txt').read().strip()
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler('start', start))
#dispatcher.add_handler(MessageHandler(Filters.location, where))
updater.start_polling()