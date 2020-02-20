import idena.emoji as emo
import idena.utils as utl
import re

from enum import auto
from idena.plugin import IdenaPlugin
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import CallbackQueryHandler, RegexHandler, CommandHandler, \
    ConversationHandler, MessageHandler, Filters


class Notify(IdenaPlugin):

    ONOFF = auto()
    DATA = auto()
    FINAL = auto()

    TYPE_TG = "Telegram"
    TYPE_EM = "E-Mail"
    TYPE_DC = "Discord"

    ONOFF_Y = "Yes"
    ONOFF_N = "No"

    CANCEL = "Cancel"

    def __enter__(self):
        self.add_handler(
            ConversationHandler(
                entry_points=[CommandHandler('notify', self.cmd_notify)],
                states={
                    self.ONOFF:
                        [CallbackQueryHandler(self.callback_onoff, pass_user_data=True)],
                    self.DATA:
                        [CallbackQueryHandler(self.callback_enable, pass_user_data=True)],
                    self.FINAL:
                        [RegexHandler(self.email_regex(), self.regex_email),
                         RegexHandler(self.discord_regex(), self.regex_discord),
                         CallbackQueryHandler(self.callback_cancel),
                         MessageHandler(Filters.text, self.message_wrong, pass_user_data=True)]
                },
                fallbacks=[CommandHandler('notify', self.cmd_notify)],
                allow_reentry=True))

        return self

    @IdenaPlugin.add_user
    @IdenaPlugin.send_typing
    def cmd_notify(self, bot, update):
        user_id = update.effective_user.id

        sql = self.get_global_resource("select_user.sql")
        res = self.execute_global_sql(sql, user_id)

        if not res["success"]:
            msg = f"{emo.ERROR} Not possible to retrieve user: {res['data']}"
            update.message.reply_text(msg)
            self.notify(msg)
            return

        if res["data"][0]:
            telegram = res["data"][0][5]
            email = res["data"][0][6]
            discord = res["data"][0][7]
        else:
            telegram = email = discord = str()

        msg = f"*Current notification settings*\n\n" \
              f"`Telegram: {'Enabled' if telegram else 'Disabled'}`\n" \
              f"`Discord : {'Enabled' if discord else 'Disabled'}`\n" \
              f"`E-Mail  : {'Enabled' if email else 'Disabled'}`\n\n" \
              f"Choose which notification type to edit"

        buttons = [
            InlineKeyboardButton(self.TYPE_TG, callback_data=self.TYPE_TG),
            InlineKeyboardButton(self.TYPE_EM, callback_data=self.TYPE_EM),
            InlineKeyboardButton(self.TYPE_DC, callback_data=self.TYPE_DC)]

        menu = utl.build_menu(buttons, n_cols=3)
        keyboard = InlineKeyboardMarkup(menu, resize_keyboard=True)

        update.message.reply_text(msg, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        return self.ONOFF

    @IdenaPlugin.send_typing
    def callback_onoff(self, bot, update, user_data):
        query = update.callback_query
        user_data["type"] = query.data

        buttons = [
            InlineKeyboardButton(self.ONOFF_Y, callback_data=self.ONOFF_Y),
            InlineKeyboardButton(self.ONOFF_N, callback_data=self.ONOFF_N)]

        menu = utl.build_menu(buttons, n_cols=2)
        keyboard = InlineKeyboardMarkup(menu, resize_keyboard=True)

        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=f"Enable {user_data['type']} notifications?",
            reply_markup=keyboard
        )

        return self.DATA

    @IdenaPlugin.send_typing
    def callback_enable(self, bot, update, user_data):
        query = update.callback_query
        user_id = query.from_user.id

        user_data["enable"] = query.data

        if user_data["enable"] == self.ONOFF_N:

            sql = str()
            if user_data["type"] == self.TYPE_TG:
                sql = self.get_resource("update_telegram.sql")
            elif user_data["type"] == self.TYPE_EM:
                sql = self.get_resource("update_email.sql")
            elif user_data["type"] == self.TYPE_DC:
                sql = self.get_resource("update_discord.sql")

            if sql:
                self.execute_global_sql(sql, None, user_id)

            bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text=f"{emo.CANCEL} {user_data['type']} notifications disabled")

            return ConversationHandler.END

        user_data["enable"] = self.ONOFF_Y

        menu = utl.build_menu([InlineKeyboardButton(self.CANCEL, callback_data=self.CANCEL)])
        keyboard = InlineKeyboardMarkup(menu, resize_keyboard=True)

        msg = str()
        if user_data["type"] == self.TYPE_TG:
            sql = self.get_resource("update_telegram.sql")
            self.execute_global_sql(sql, user_id, user_id)

            bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text=f"{emo.CHECK} {self.TYPE_TG} notifications enabled"
            )

            return ConversationHandler.END
        elif user_data["type"] == self.TYPE_EM:
            msg = f"Please send me your {self.TYPE_EM} address or press {self.CANCEL}"
        elif user_data["type"] == self.TYPE_DC:
            msg = f"Please send me your {self.TYPE_DC} ID or press {self.CANCEL}"

        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=msg,
            reply_markup=keyboard
        )

        return self.FINAL

    @IdenaPlugin.send_typing
    def message_wrong(self, bot, update, user_data):
        msg = str()
        if user_data["type"] == self.TYPE_EM:
            msg = f"Not a valid email address. Send again"
        elif user_data["type"] == self.TYPE_DC:
            msg = f"Not a valid Discord ID. Send again"

        update.message.reply_text(msg)
        return self.FINAL

    def callback_cancel(self, bot, update):
        query = update.callback_query

        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=f"{emo.INFO} Notifications not changed"
        )

        return ConversationHandler.END

    @IdenaPlugin.send_typing
    def regex_email(self, bot, update):
        email = update.message.text
        user_id = update.effective_user.id

        sql = self.get_resource("update_email.sql")
        self.execute_global_sql(sql, email, user_id)

        update.message.reply_text(f"{emo.CHECK} {self.TYPE_EM} notifications enabled")
        return ConversationHandler.END

    @IdenaPlugin.send_typing
    def regex_discord(self, bot, update):
        discord = update.message.text
        user_id = update.effective_user.id

        sql = self.get_resource("update_discord.sql")
        self.execute_global_sql(sql, discord, user_id)

        update.message.reply_text(f"{emo.CHECK} {self.TYPE_DC} notifications enabled")
        return ConversationHandler.END

    # Returns pre compiled Regex pattern for EMail addresses
    def email_regex(self):
        pattern = "(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        return re.compile(pattern, re.IGNORECASE)

    # Returns pre compiled Regex pattern for Discord tags
    def discord_regex(self):
        pattern = "(.*)#(\d{4})"
        return re.compile(pattern, re.IGNORECASE)

    @IdenaPlugin.threaded
    @IdenaPlugin.add_user
    @IdenaPlugin.send_typing
    def execute(self, bot, update, args):
        # Not used since we already defined a ConversationHandler
        pass
