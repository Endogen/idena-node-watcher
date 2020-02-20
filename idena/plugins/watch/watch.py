import re
import ssl
import time
import smtplib
import logging
import requests
import idena.emoji as emo

from random import randrange
from datetime import datetime
from telegram import ParseMode
from idena.plugin import IdenaPlugin


class Watch(IdenaPlugin):

    # At bot start, start jobs to watch all nodes
    def __enter__(self):
        # Get all node addresses
        sql = self.get_resource("select_nodes.sql")
        res = self.execute_global_sql(sql)

        if not res["success"]:
            msg = "Not possible to read nodes from database"
            self.notify(f"{emo.ERROR} {msg}")
            logging.error(msg)
            return self

        # Go through each node and create repeating job to check it
        for address in res["data"]:
            address = address[0]

            self.repeat_job(
                self.check_node,
                self.config.get("check_time"),
                first=randrange(0, 60),
                context={"address": address, "online": None},
                name=address)

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
        if not re.compile("^0x[a-fA-F0-9]{40}$").match(address):
            update.message.reply_text(
                f"{emo.ERROR} The provided address is not valid",
                parse_mode=ParseMode.MARKDOWN)
            return

        # Check if user is already watching this node
        sql = self.get_resource("node_exists.sql")
        res = self.execute_global_sql(sql, user_id, address)

        if res["data"]:
            update.message.reply_text(
                f"{emo.INFO} You are already watching this node",
                parse_mode=ParseMode.MARKDOWN)
            return

        # Save node in database
        sql = self.get_resource("insert_node.sql")
        res = self.execute_global_sql(sql, user_id, address)

        if not res["success"]:
            msg = f"{emo.ERROR} Not possible to add node: {res['data']}"
            update.message.reply_text(msg)
            self.notify(msg)
            return

        # Check if there is already a job to watch this node
        if not self.get_job(address):
            context = {"address": address, "online": None}

            self.repeat_job(
                self.check_node,
                self.config.get("check_time"),
                context=context,
                name=address)

        update.message.reply_text(f"{emo.CHECK} Node is being watched")

    # Job logic to watch a node
    def check_node(self, bot, job):
        address = job.context['address']

        api_url = self.config.get("api_url")
        api_url = f"{api_url}{address}"

        try:
            # Read IDENA explorer API to know when node was last seen
            response = requests.get(api_url, timeout=self.config.get("api_timeout")).json()
        except Exception as e:
            msg = f"{address} Could not reach API: {e}"
            logging.error(msg)
            return

        # If no last seen date-time, stop to watch node
        if not response or not response["result"] or not response["result"]["lastActivity"]:
            msg = "No 'Last Seen' date. Can not watch node"
            logging.error(f"{address} {msg}")
            job.schedule_removal()

            # Get all users that watch this node
            sql = self.get_resource("select_notify.sql")
            res = self.execute_global_sql(sql, address)

            if not res["success"]:
                msg = f"{address} No data found: {res['data']}"
                logging.error(msg)
                return

            # Send message to all users that watch this node
            for data in res["data"]:
                try:
                    # Send message that watching this node is not possible
                    bot.send_message(data[0], f"{emo.ERROR} {msg}", parse_mode=ParseMode.MARKDOWN)
                except Exception as e:
                    msg = f"{address} Can't reply to user: {e}"
                    logging.error(msg)

            # Remove node from database
            sql = self.get_resource("delete_node.sql")
            self.execute_global_sql(sql, address)

            return

        # Extract last seen date-time and convert it to seconds
        last_seen = response["result"]["lastActivity"].split(".")[0]
        last_seen_date = datetime.strptime(last_seen, "%Y-%m-%dT%H:%M:%S")
        last_seen_sec = (last_seen_date - datetime(1970, 1, 1)).total_seconds()

        # Load allowed time delta and calculate actual time delta
        allowed_delta = int(self.config.get("time_delta"))
        current_delta = int(time.time() - last_seen_sec)

        # Allowed time delta exceeded --> node is offline
        if current_delta > allowed_delta:
            if job.context['online']:
                job.context['online'] = False

                logging.info(f"{address} Node went offline "
                             f"- {last_seen_date} "
                             f"- {allowed_delta}/{current_delta}")

                # Create IDENA explorer link to identity
                identity_url = f"{self.config.get('identity_url')}{address}"

                msg = f"IDENA node is *OFFLINE*\n" \
                      f"[{address[:12]}...{address[-12:]}]({identity_url})"

                # Get all users that watch this node
                sql = self.get_resource("select_notify.sql")
                res = self.execute_global_sql(sql, address)

                if not res["success"]:
                    msg = f"{address} No data found: {res['data']}"
                    logging.error(msg)
                    return

                # Notify user
                for data in res["data"]:
                    # Telegram
                    if data[0]:
                        try:
                            bot.send_message(
                                data[0],
                                f"{emo.ALERT} {msg}",
                                parse_mode=ParseMode.MARKDOWN,
                                disable_web_page_preview=True)
                            logging.info(f"{address} Notification (Telegram) sent - {data}")
                        except Exception as e:
                            msg = f"{address} Can't notify user {data[0]} via Telegram: {e}"
                            logging.error(msg)

                    # Email
                    if data[1]:
                        try:
                            smtp = self.global_config.get("notify", "email", "smtp")
                            port = self.global_config.get("notify", "email", "port")
                            mail = self.global_config.get("notify", "email", "mail")
                            user = self.global_config.get("notify", "email", "user")
                            pswd = self.global_config.get("notify", "email", "pass")
                            subject = self.global_config.get("notify", "email", "subject")
                            message = self.global_config.get("notify", "email", "message")
                            message = str(message).replace("{{node}}", address)

                            context = ssl.create_default_context()
                            with smtplib.SMTP_SSL(smtp, port, context=context) as server:
                                server.login(user, pswd)
                                server.sendmail(mail, data[1], f"Subject: {subject}\n\n{message}")
                                logging.info(f"{address} Notification (EMail) sent - {data}")
                        except Exception as e:
                            msg = f"{address} Can't notify user {data[0]} via EMail: {e}"
                            logging.error(msg)

                    # Discord
                    if data[2]:
                        # TODO: Not yet implemented
                        pass
            else:
                logging.info(f"{address} Node is offline "
                             f"- {last_seen_date} "
                             f"- {allowed_delta}/{current_delta}")
        else:
            job.context['online'] = True
            logging.info(f"{address} Node is online "
                         f"- {last_seen_date} "
                         f"- {allowed_delta}/{current_delta}")
