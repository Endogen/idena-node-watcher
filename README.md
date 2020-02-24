# IDENA Node Watcher

*IDENA Node Watcher* is a Telegram bot created by Telegram user @endogen for the IDENA community. The bot can monitor one or more IDENA nodes for you and notify you if one of them goes down.

## Overview

The bot is build around the [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) module and is polling based. [Webhook mode](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks) is implemented but untested.

### General bot features

- Every command is a plugin
- Every plugin can be updated by sending the plugin file to the bot
- Restart or shutdown the bot via command
- Bot can be administered by more then one user
- Commands to backup the bot or view latest logs are available

### IDENA specific features

- Add one or more nodes to be watched by the bot
- List all your watched node and verify that they are being watched
- Remove nodes that you don&#39;t want to watch anymore
- Change type of notification
  - Telegram
  - Email

## Configuration

Before starting up the bot you have to take care of some settings and add a Telegram API token. The configuration file and token file are located in the `config` folder.

### config.json

This file holds the configuration for the bot. You have to at least edit the value of __ids__. Everything else is optional.

- __admin - ids__: This is a list of Telegram user IDs that will be able to control the bot. You can also add multiple users if you want. If you don&#39;t know your Telegram user ID, get in a conversation with Telegram bot [@userinfobot](https://t.me/userinfobot) and if you write him (anything) he will return you your user ID.
- __admin - notify_on_error__: If set to `true` then all user IDs in the __admin - ids__ list will be notified if some error comes up.
- __telegram - read_timeout__: Read timeout in seconds as integer. Usually this value doesn&#39;t have to be changed.
- __telegram - connect_timeout__: Connect timeout in seconds as integer. Usually this value doesn&#39;t have to be changed.
- __use_webhook__: If `true` then webhook settings will be applied. If `false` then polling will be used.
- __webhook - listen__: Required only for webhook mode. IP to listen to.
- __webhook - port__: Required only for webhook mode. Port to listen on.
- __webhook - privkey_path__: Required only for webhook mode. Path to private key (.pem file).
- __webhook - cert_path__: Required only for webhook mode. Path to certificate (.pem file).
- __webhook - url__: Required only for webhook mode. URL under which the bot is hosted.

### token.json

This file holds the Telegram bot token. You have to provide one and you will get it in a conversation with Telegram bot [@BotFather](https://t.me/BotFather) while registering your bot.

If you don&#39;t want to provide the token in a file then you have two other options:

- Provide it as a command line argument while starting your bot: `-tkn <your token>`
- Provide it as an command line input (**MOST SECURE**): `--input-tkn`

## Starting

In order to run the bot you need to execute it with the Python interpreter. If you don&#39;t have any idea where to host the bot, take a look at [Where to host Telegram Bots](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Where-to-host-Telegram-Bots). Services like [Heroku](https://www.heroku.com) (free) will work fine. You can also run the script locally on your own computer for testing purposes.

This guide is assuming that you want to run the bot on a Unix based system (Linux or macOS).

### Prerequisites

You have to use at least __Python 3.7__ to execute the scripts. Everything else is not supported.

### Installation

Install all needed Python modules

```shell
pip3 install -r requirements.txt  
```

### Starting

1. First you have to make the script `run.sh` executable with
  

```shell
chmod +x run.sh  
```

2. Then you need to start the script with

```shell
./run.sh &  
```

### Stopping

The recommended way to stop the bot is by using the bot command `/shutdown`. If you don&#39;t want or can&#39;t use this, you can shut the bot down with:

```shell
pkill python3.7  
```

which will kill __every__ Python 3.7 process that is currently running.

## Usage

### Available commands

##### Bot

```
/about - Show info about the bot  
/backup - Backup whole bot folder  
/help - Show all available commands  
/log - Download current logfile  
/restart - Restart the bot  
/shutdown - Shutdown the bot  
```

##### Node Watcher

```
/watch - Add new node to watch  
/list - Show all your watched nodes  
/notify - Set or change notification settings  
```

If you want to autocomplete available commands as you type in the chat with the bot, open a chat with Telegram bot [@BotFather](https://t.me/BotFather) and execute the command `/setcommands`. Then choose the bot you want to activate the autocomplete function for and after that send the list of commands with their descriptions. Something like this:

```
about - Show info about the bot  
backup - Backup whole bot folder  
help - Show all available commands  
log - Download current logfile  
restart - Restart the bot  
shutdown - Shutdown the bot
watch - Add new node to watch  
list - Show all your watched nodes
notify - Change notification settings  
```