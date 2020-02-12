import os
import idena.emoji as emo
import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from telegram import ParseMode
from idena.plugin import IdenaPlugin


class Check(IdenaPlugin):

    _URL = "https://scan.idena.io/identity?identity="

    def __enter__(self):
        if self.config.get("job_autostart"):
            # Start job to check if node is still mining
            interval = self.config.get("job_interval")
            self.repeat_job(self._node_check, interval)

            # Save info that node check is active
            self.config.set(True, "job_running")
        return self

    @IdenaPlugin.threaded
    @IdenaPlugin.send_typing
    def execute(self, bot, update, args):
        if len(args) > 0:
            argument = args[0].lower()

            if argument == "on":
                if self.config.get("job_running"):
                    msg = f"{emo.INFO} Node check already active"
                    update.message.reply_text(msg)
                    return

                # Start job to check if node is still mining
                interval = self.config.get("job_interval")
                self.repeat_job(self._node_check, interval)

                # Save info that node check is active
                self.config.set(True, "job_running")

                msg = f"{emo.CHECK} Node check activated"
                update.message.reply_text(msg)

            elif argument == "off":
                if not self.config.get("job_running"):
                    msg = f"{emo.INFO} Node check already deactivated"
                    update.message.reply_text(msg)
                    return

                # Stop job to check if node is still mining
                self.get_job(self.get_name()).schedule_removal()

                # Save info that node check if deactivated
                self.config.set(False, "job_running")

                msg = f"{emo.CHECK} Node check deactivated"
                update.message.reply_text(msg)

        else:
            address = self.api().address()

            if "error" in address:
                error = address["error"]["message"]
                msg = f"{emo.ERROR} Couldn't retrieve address: {error}"
                update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
                logging.error(msg)
                return

            result = self.check_mining(address['result'])

            if result["success"]:
                if result["message"]:
                    msg = result["message"]
                else:
                    msg = f"Mining Status: `{result['mining']}`\n" \
                          f"Last Seen: `{result['last_seen']}`"
            else:
                msg = f"{emo.ERROR} {result['message']}"

            update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    def _node_check(self, bot, job):
        address = self.api().address()

        if "error" in address:
            error = address["error"]["message"]
            msg = f"{emo.ERROR} Couldn't retrieve address: {error}"
            logging.error(msg)
            return

        result = self.check_mining(address['result'])

        if result["success"]:
            mining = result["mining"]
            last_seen = result["last_seen"]

            if mining and mining != "On":
                # Send notification to admins
                for admin in self.global_config.get("admin", "ids"):
                    try:
                        msg = f"{emo.ALERT} *Node is not mining!*\nLast seen: {last_seen}"
                        bot.send_message(admin, msg, parse_mode=ParseMode.MARKDOWN)
                    except Exception as e:
                        msg = f"Couldn't send notification that node is not mining to ID {str(admin)}: {e}"
                        logging.warning(msg)

    def check_mining(self, address):
        options = Options()
        options.add_argument("--headless")
        options.binary_location = self.config.get("chrome_path")

        path = os.path.join(self.get_res_path(plugin=self.get_name()), "chromedriver")

        result = {"success": None, "message": None, "mining": None, "last_seen": None}
        driver = None

        try:
            driver = webdriver.Chrome(executable_path=path, chrome_options=options)
            driver.get(f"{self._URL}{address}")

            mining = driver.find_element_by_id("OnlineMinerStatus").text
            last_seen = driver.find_element_by_id("LastSeen").text
        except Exception as e:
            msg = f"{emo.ERROR} Not possible to read 'Last Seen' date: {e}"

            result["success"] = False
            result["message"] = msg

            logging.error(msg)
            return result
        finally:
            if driver:
                driver.close()

        result["success"] = True

        if mining:
            result["mining"] = mining
            result["last_seen"] = last_seen
        else:
            result["message"] = f"{emo.CANCEL} Mining not possible"

        return result
