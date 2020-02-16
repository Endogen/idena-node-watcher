import idena.emoji as emo
import idena.utils as utl

from idena.plugin import IdenaPlugin
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler


class List(IdenaPlugin):

    def __enter__(self):
        self.add_handler(CallbackQueryHandler(self._callback))
        return self

    @IdenaPlugin.threaded
    @IdenaPlugin.add_user
    @IdenaPlugin.send_typing
    def execute(self, bot, update, args):
        user_id = update.effective_user.id

        sql = self.get_resource("select_nodes.sql")
        res = self.execute_global_sql(sql, user_id)

        if not res["success"]:
            msg = f"{emo.ERROR} Not possible to retrieve watched nodes: {res['data']}"
            update.message.reply_text(msg)
            self.notify(msg)
            return

        if not res["data"]:
            msg = f"{emo.INFO} No watched nodes found"
            update.message.reply_text(msg)
            return

        for data in res["data"]:
            rowid = data[0]
            user_id = data[1]
            address = data[2]

            identity_url = f"{self.config.get('identity_url')}{address}"
            msg = f"[{address[:12]}...{address[-12:]}]({identity_url})"

            try:
                bot.send_message(
                    user_id,
                    msg,
                    reply_markup=self._remove_button(rowid),
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True)
            except Exception as e:
                msg = f"{emo.ERROR} Not possible to send watched node list: {res['data']}"
                update.message.reply_text(msg)
                self.notify(msg)

    def _remove_button(self, row_id):
        menu = utl.build_menu([InlineKeyboardButton("Remove from Watchlist", callback_data=row_id)])
        return InlineKeyboardMarkup(menu, resize_keyboard=True)

    def _callback(self, bot, update):
        query = update.callback_query
        query.message.delete()

        sql = self.get_resource("delete_node.sql")
        self.execute_global_sql(sql, query.data)

        msg = f"{emo.CHECK} Node removed"
        bot.answer_callback_query(query.id, msg)
