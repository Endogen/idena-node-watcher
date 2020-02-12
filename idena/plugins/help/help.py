from collections import OrderedDict

from telegram import ParseMode
from idena.plugin import IdenaPlugin


class Help(IdenaPlugin):

    @IdenaPlugin.threaded
    @IdenaPlugin.send_typing
    def execute(self, bot, update, args):
        categories = OrderedDict()

        for p in self.get_plugins():
            if p.get_category() and p.get_description():
                des = f"/{p.get_handle()} - {p.get_description()}"

                if p.get_category() not in categories:
                    categories[p.get_category()] = [des]
                else:
                    categories[p.get_category()].append(des)

        msg = "*Available commands*\n\n"

        for category in sorted(categories):
            msg += f"*{category}*\n"

            for cmd in sorted(categories[category]):
                msg += f"{cmd}\n"

            msg += "\n"

        update.message.reply_text(
            text=msg,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True)
