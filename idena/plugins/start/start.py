from telegram import ParseMode
from idena.plugin import IdenaPlugin


class Start(IdenaPlugin):

    INTRO_FILE = "intro.md"

    def __enter__(self):
        if not self.global_table_exists("users"):
            sql = self.get_resource("create_users.sql")
            self.execute_global_sql(sql)
        if not self.global_table_exists("nodes"):
            sql = self.get_resource("create_nodes.sql")
            self.execute_global_sql(sql)
        return self

    @IdenaPlugin.add_user
    @IdenaPlugin.threaded
    def execute(self, bot, update, args):
        user = update.effective_user

        intro = self.get_resource(self.INTRO_FILE)
        intro = intro.replace("{{firstname}}", user.first_name)

        update.message.reply_text(intro, parse_mode=ParseMode.MARKDOWN)
