import time
import logging
import requests
import idena.emoji as emo

from datetime import datetime
from telegram import ParseMode
from idena.plugin import IdenaPlugin


# TODO: Add two workflows: 1) Adding via arguemnts 2) Adding by guiding through workflow
class Watch(IdenaPlugin):

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

        sql = self.get_resource("node_exists.sql")
        res = self.execute_global_sql(sql, user_id, address)

        if res["data"]:
            update.message.reply_text(
                f"{emo.INFO} You are already watching this node",
                parse_mode=ParseMode.MARKDOWN)
            return

        period = self.config.get("check_time")

        sql = self.get_resource("insert_node.sql")
        res = self.execute_global_sql(sql, user_id, address, period)

        if not res["success"]:
            msg = f"{emo.ERROR} Not possible to add node: {res['data']}"
            update.message.reply_text(msg)
            self.notify(msg)
            return

        context = {"address": address, "update": update, "online": None}

        self.repeat_job(
            self.check_node,
            period,
            context=context,
            name=address)

    def check_node(self, bot, job):
        address = job.context['address']
        update = job.context['update']

        timeout = self.config.get("api_timeout")

        api_url = self.config.get("api_url")
        api_url = f"{api_url}{address}"

        try:
            response = requests.get(api_url, timeout=timeout).json()
        except Exception as e:
            msg = f"{address} Could not reach API: {e}"
            logging.error(msg)
            return

        if not response or not response["result"] or not response["result"]["lastActivity"]:
            msg = "No 'Last Seen' date. Can not watch node"
            logging.error(f"{address} {msg}")
            job.schedule_removal()

            try:
                update.message.reply_text(f"{emo.ERROR} {msg}", parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                msg = f"{address} Can't reply to user: {e} - {update}"
                logging.error(msg)
            return

        last_seen = response["result"]["lastActivity"].split(".")[0]
        last_seen_date = datetime.strptime(last_seen, "%Y-%m-%dT%H:%M:%S")
        last_seen_sec = (last_seen_date - datetime(1970, 1, 1)).total_seconds()

        allowed_delta = int(self.config.get("time_delta"))
        current_delta = int(time.time() - last_seen_sec)

        if current_delta > allowed_delta:
            if job.context['online']:
                job.context['online'] = False

                logging.info(f"{address} Node went offline "
                             f"- {last_seen_date} "
                             f"- {allowed_delta}/{current_delta}")

                identity_url = f"{self.config.get('identity_url')}{address}"
                msg = f"IDENA NODE IS *OFFLINE*\n[{address[:13]}...{address[-13:]}]({identity_url})"

                try:
                    update.message.reply_text(
                        f"{emo.ALERT} {msg}",
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True)
                except Exception as e:
                    msg = f"{address} Can't reply to user: {e} - {update}"
                    logging.error(msg)
            else:
                logging.info(f"{address} Node is offline "
                             f"- {last_seen_date} "
                             f"- {allowed_delta}/{current_delta}")
        else:
            job.context['online'] = True
            logging.info(f"{address} Node is online "
                         f"- {last_seen_date} "
                         f"- {allowed_delta}/{current_delta}")
