import os

# Project folders
DIR_SRC = os.path.basename(os.path.dirname(__file__))
DIR_RES = "resources"
DIR_PLG = "plugins"
DIR_CFG = "config"
DIR_LOG = "logs"
DIR_DAT = "data"
DIR_TMP = "temp"

# Project files
FILE_DAT = "global.db"
FILE_CFG = "config.json"
FILE_TKN = "token.json"
FILE_LOG = f"{DIR_SRC}.log"

# Max Telegram message length
MAX_TG_MSG_LEN = 4096
