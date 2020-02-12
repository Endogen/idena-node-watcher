import os
import signal
import threading
import idena.emoji as emo

from idena.plugin import IdenaPlugin


class Shutdown(IdenaPlugin):

    @IdenaPlugin.owner
    @IdenaPlugin.threaded
    @IdenaPlugin.send_typing
    def execute(self, bot, update, args):
        msg = f"{emo.GOODBYE} Shutting down..."
        update.message.reply_text(msg)

        threading.Thread(target=self._shutdown_thread).start()

    # TODO: Remove access to protected variable
    def _shutdown_thread(self):
        self._tgb.updater.stop()
        self._tgb.updater.is_idle = False
        os.kill(os.getpid(), signal.SIGINT)
