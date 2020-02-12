from telegram import ParseMode
from idena.plugin import IdenaPlugin


class About(IdenaPlugin):

    INFO_FILE = "info.md"

    @IdenaPlugin.threaded
    @IdenaPlugin.send_typing
    def execute(self, bot, update, args):
        update.message.reply_text(
            text=self.get_resource(self.INFO_FILE),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True)
