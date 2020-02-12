import os
import logging
import idena.emoji as emo
import idena.constants as con

from idena.plugin import IdenaPlugin


class Logfile(IdenaPlugin):

    @IdenaPlugin.owner
    @IdenaPlugin.private
    @IdenaPlugin.threaded
    @IdenaPlugin.send_typing
    def execute(self, bot, update, args):
        base_dir = os.path.abspath(os.getcwd())
        log_file = os.path.join(base_dir, con.DIR_LOG, con.FILE_LOG)

        if os.path.isfile(log_file):
            try:
                file = open(log_file, 'rb')
            except Exception as e:
                logging.error(e)
                self.notify(e)
                file = None
        else:
            file = None

        if file:
            update.message.reply_document(
                caption=f"{emo.CHECK} Current Logfile",
                document=file)
        else:
            update.message.reply_text(
                text=f"{emo.ERROR} Not possible to download logfile")
