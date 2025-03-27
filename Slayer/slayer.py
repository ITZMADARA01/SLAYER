from bot import Bot

class Slayer(Bot):
    def __init__(self):
        super().__init__()

    def slayer_command(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id, text='Slayer command!')

    def add_slayer_handlers(self):
        dispatcher = self.updater.dispatcher
        slayer_handler = CommandHandler('slayer', self.slayer_command)
        dispatcher.add_handler(slayer_handler)
