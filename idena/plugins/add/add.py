import os
import logging
import idena.emoji as emo

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from telegram import ParseMode
from idena.plugin import IdenaPlugin


# TODO: Add two workflows: 1) Adding via arguemnts 2) Adding by guiding through workflow
class Add(IdenaPlugin):

    _URL = "https://scan.idena.io/identity?identity="

    def __enter__(self):
        options = Options()
        options.add_argument("--headless")
        options.binary_location = self.config.get("chrome_path")

        path = os.path.join(self.get_res_path(plugin=self.get_name()), "chromedriver")

        self.driver = webdriver.Chrome(executable_path=path, chrome_options=options)
        return self

    @IdenaPlugin.threaded
    @IdenaPlugin.add_user
    @IdenaPlugin.send_typing
    def execute(self, bot, update, args):
        user_id = update.effective_user.id

        if len(args) != 1:
            update.message.reply_text(
                self.get_usage(),
                parse_mode=ParseMode.MARKDOWN)
            return

        address = str(args[0])

        # Check if provided wallet address is valid
        if not address.startswith("0x") or len(address) != 42:
            update.message.reply_text(
                f"{emo.ERROR} The provided address is not a valid",
                parse_mode=ParseMode.MARKDOWN)
            return

        # TODO: Read this value from ConversationHandler
        period = 30

        sql = self.get_resource("node_exists.sql")
        res = self.execute_global_sql(sql, user_id, address)

        if res["data"]:
            update.message.reply_text(
                f"{emo.INFO} You are already watching this node",
                parse_mode=ParseMode.MARKDOWN)
            return

        sql = self.get_resource("insert_node.sql")
        res = self.execute_global_sql(sql, user_id, address, period)

        if not res["success"]:
            msg = f"{emo.ERROR} Not possible to add node: {res['data']}"
            update.message.reply_text(msg)
            self.notify(msg)
            return

        self.repeat_job(
            self.check_node,
            period,
            context={"address": address, "update": update},
            name=address)

    def check_node(self, bot, job):
        address = job.context['address']
        update = job.context['update']

        try:
            self.driver.get(f"{self._URL}{address}")
            last_seen = self.driver.find_element_by_id("LastSeen").text
        except Exception as e:
            msg = f"{emo.ERROR} Not possible to read 'Last Seen' for {address}: {e}"
            logging.error(msg)
            return

        if not last_seen:
            msg = f"{emo.CANCEL} No 'Last Seen' value. Node will be removed from watch list"
            update.message.reply_text(msg)
            job.schedule_removal()
            return

        # TODO: Analyze if time frame already passed
