#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import sys
import datetime
import time
import telepot
from telepot.loop import MessageLoop
from pyzotero import zotero


# Credentials
## Telegram
TOKEN = ""
CHAT_TITLE = ""
CHAT_ID = ""
## Zotero
library_type = 'user'
library_id = ''
api_key = ''


if os.path.isfile('config.json'):
    with open('config.json', 'r') as f:
        config = json.load(f)
        if config['telegram']['token'] == "":
            sys.exit("No token defined. Define it in a file called config.json.")
        if config['telegram']['chat_title'] == "":
            sys.exit("Empty chat title. Define it in a file called config.json.")
        if config['telegram']['chat_id'] == "":
            sys.exit("Empty chat id. Define it in a file called config.json.")
        TOKEN = config['telegram']['token']
        CHAT_TITLE = config['telegram']['chat_title']
        CHAT_ID = int(config['telegram']['chat_id'])
        # Zotero credentials
        if config['zotero']['library_id'] == "":
            sys.exit("No Zotero personal library ID defined. Define it in a file called config.json.")
        if config['zotero']['api_key'] == "":
            sys.exit("No Zotero API key defined. Define it in a file called config.json")
        if config['zotero']['library_type'] == "":
            print("WARNING: Empty Zotero library type. Assuming to use your own Zotero library, not a shared group library.")
        library_type = config['zotero']['library_type']
        library_id = config['zotero']['library_id']
        api_key = config['zotero']['api_key']
else:
    sys.exit("No config file found. Remember changing the name of config-sample.json to config.json")

def handle_zotero(msg):
    # Check for a valid telegram message of entity type 'url'.
    # This message gets parsed and is forwarded/saved to Zotero.
    
    if 'document' in msg:
        return "Can not add documents Zotero."

    if 'text' not in msg:
        return "Can only add text of type 'url' to Zotero."

    # ToDo: Improve parsing entities  
    if 'entities' in msg:
        if 'type' in msg['entities'][0]:
            if msg['entities'][0]['type'] == "url":
                print("Valid message of type 'url'.")
            else:
                print("Message not of type 'url'.")
    else:
        return "Cannot add to Zotero: Message is not of type 'url'"

    # Parse url and text from message
    url_offset = msg['entities'][0]['offset']
    url_length = msg['entities'][0]['length']
    url = msg['text'][url_offset:]
    #if len(url) != url_length:
    #    return "Error at parsing URL: length does not match."
    url_title = msg['text'][:url_offset]
    url_date = datetime.datetime.fromtimestamp(msg['date'])

    # "Allow write access" must be enabled to allow changes to your library
    # Prepare new Zotero object from template
    newItem = zot.item_template('blogPost')
    newItem['title'] = url_title
    newItem['url'] = url
    newItem['accessDate'] = url_date.strftime("%Y-%m-%d %H:%M:%S")
    newItem['tags'] = [{'tag': 'FromAndroid'}, {'tag': 'Unfiled'}] # ToDo: Stored as unfiled anyway.

    createdItem = zot.create_items([newItem])
    print(createdItem)
    
    if len(createdItem['failed']) != 0:
        return "Error " + str(createdItem['failed']['0']['code']) + " at attempt to write to Zotero: " + createdItem['failed']['0']['message']
    elif len(createdItem['success']) != 0:
        return "Item " + str(createdItem['success']['0']) + " saved to Zotero."
    else:
        return "Unknown error creating Zotero item."


def is_allowed(chat_title, chat_id):
    if (chat_title == CHAT_TITLE) and (chat_id == CHAT_ID):
        return True
    else:
        return False


def on_chat_message(msg):
    print("Message: " + str(msg))
    content_type, chat_type, chat_id = telepot.glance(msg)

    if chat_type != 'channel':
        bot.sendMessage(chat_id, "Only valid for channels.")
        return

    if not is_allowed(msg['chat']['title'], chat_id):
        bot.sendMessage(chat_id, "Chat title or id does not match the configuration.")
        return 

    ret = handle_zotero(msg) # Handle message to save it to Zotero
    bot.sendMessage(chat_id, ret) # Let bot send message back to user


bot = telepot.Bot(TOKEN)
zot = zotero.Zotero(library_id, library_type, api_key)
zot.key_info() # Checks for successful permissions of Zotero instance.

MessageLoop(bot, on_chat_message).run_as_thread()
print('Listening ...')
# Keep the program running.
while 1:
    time.sleep(10)
