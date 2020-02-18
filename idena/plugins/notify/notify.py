import idena.emoji as emo
import idena.utils as utl

from idena.plugin import IdenaPlugin
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler


class Notify(IdenaPlugin):

    def __enter__(self):
        self.add_handler(CallbackQueryHandler(self._callback_type), group=1)
        self.add_handler(CallbackQueryHandler(self._callback_setting), group=2)
        return self

    @IdenaPlugin.threaded
    @IdenaPlugin.add_user
    @IdenaPlugin.send_typing
    def execute(self, bot, update, args):
        name = update.effective_user.first_name

        msg = f"Hey {name} choose which notification type you want to adjust"
        update.message.reply_text(msg, reply_markup=self._notification_type())

        user_id = update.effective_user.id

        sql = self.get_global_resource("select_user.sql")
        res = self.execute_global_sql(sql, user_id)

        if not res["success"]:
            msg = f"{emo.ERROR} Not possible to retrieve user: {res['data']}"
            update.message.reply_text(msg)
            self.notify(msg)
            return

        for data in res["data"]:
            telegram = data[5]
            email = data[6]
            discord = data[7]

    def _notification_type(self):
        buttons = [
            InlineKeyboardButton("Telegram", callback_data="notify_type_telegram"),
            InlineKeyboardButton("EMail", callback_data="notify_type_mail"),
            InlineKeyboardButton("Discord", callback_data="notify_type_discord")]

        menu = utl.build_menu(buttons, n_cols=3)
        return InlineKeyboardMarkup(menu, resize_keyboard=True)

    def _notification_telegram(self):
        buttons = [
            InlineKeyboardButton("Yes", callback_data="notify_setting_tg_yes"),
            InlineKeyboardButton("No", callback_data="notify_setting_tg_no")]

        menu = utl.build_menu(buttons, n_cols=2)
        return InlineKeyboardMarkup(menu, resize_keyboard=True)

    def _notification_email(self):
        buttons = [
            InlineKeyboardButton("Yes", callback_data="notify_setting_mail_yes"),
            InlineKeyboardButton("No", callback_data="notify_setting_mail_no")]

        menu = utl.build_menu(buttons, n_cols=2)
        return InlineKeyboardMarkup(menu, resize_keyboard=True)

    def _notification_discord(self):
        buttons = [
            InlineKeyboardButton("Yes", callback_data="notify_setting_dis_yes"),
            InlineKeyboardButton("No", callback_data="notify_setting_dis_no")]

        menu = utl.build_menu(buttons, n_cols=2)
        return InlineKeyboardMarkup(menu, resize_keyboard=True)

    def _callback_type(self, bot, update):
        user_id = update.effective_user.id
        query = update.callback_query

        if not str(query.data).startswith("notify_type_"):
            return

        query.message.delete()

        if query.data == "notify_type_telegram":
            msg = f"Enable Telegram notifications?"
            bot.send_message(user_id, msg, reply_markup=self._notification_telegram())
        elif query.data == "notify_type_mail":
            msg = f"Enable EMail notifications?"
            bot.send_message(user_id, msg, reply_markup=self._notification_email())
        elif query.data == "notify_type_discord":
            msg = f"Enable Discord notifications?"
            bot.send_message(user_id, msg, reply_markup=self._notification_discord())

        else:
            bot.answer_callback_query(query.id, f"{emo.ERROR} ERROR")

    def _callback_setting(self, bot, update):
        user_id = update.effective_user.id
        query = update.callback_query

        if not str(query.data).startswith("notify_setting_"):
            return

        query.message.delete()

        if query.data == "notify_setting_tg_yes":
            msg = f"{emo.CHECK} Telegram notifications enabled"
            bot.send_message(user_id, msg)
        elif query.data == "notify_setting_tg_no":
            msg = f"{emo.CANCEL} Telegram notifications disabled"
            bot.send_message(user_id, msg)

        elif query.data == "notify_setting_mail_yes":
            msg = f"{emo.CHECK} EMail notifications enabled"
            bot.send_message(user_id, msg)
        elif query.data == "notify_setting_mail_no":
            msg = f"{emo.CANCEL} EMail notifications disabled"
            bot.send_message(user_id, msg)

        elif query.data == "notify_setting_dis_yes":
            msg = f"{emo.CHECK} Discord notifications enabled"
            bot.send_message(user_id, msg)
        elif query.data == "notify_setting_dis_no":
            msg = f"{emo.CANCEL} Discord notifications disabled"
            bot.send_message(user_id, msg)

        else:
            bot.answer_callback_query(query.id, f"{emo.ERROR} ERROR")
            return

        bot.answer_callback_query(query.id, f"{emo.INFO} Done")
