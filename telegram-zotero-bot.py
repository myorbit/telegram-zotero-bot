#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os

import sys
import datetime
import telepot
import time
from telepot.loop import MessageLoop
from pyzotero import zotero

def save_status(obj):
    with open('chats.json', 'w') as f:
        f.write(json.dumps(obj))

def save_allowed(s):
    with open('allowed.json', 'w') as f:
        f.write(json.dumps(list(s)))

if not os.path.isfile('chats.json'):
    save_status({})

if not os.path.isfile('allowed.json'):
    save_allowed(set())

# Credentials
## Telegram
chats = {}
allowed = []
TOKEN = ""
PASSWORD = "changeme"
CHAT_TITLE = "ZoteroStore"
## Zotero
library_type = 'user'
library_id = ''
api_key = ''


with open('chats.json', 'r') as f:
    chats = json.load(f)

with open('allowed.json', 'r') as f:
    allowed = set(json.load(f))

if os.path.isfile('config.json'):
    with open('config.json', 'r') as f:
        config = json.load(f)
        if config['token'] == "":
            sys.exit("No token defined. Define it in a file called config.json.")
        if config['password'] == "":
            print("WARNING: Empty Password for registering to use the bot." +
                  " It could be dangerous, because anybody could use this bot" +
                  " and forward messages to the channels associated to it")
        TOKEN = config['token']
        PASSWORD = config['password']
        # Zotero credentials
        if config['zotero_library_id'] == "":
            sys.exit("No Zotero personal library ID defined. Define it in a file called config.json.")
        if config['zotero_api_key'] == "":
            sys.exit("No Zotero API key defined. Define it in a file called config.json")
        if config['zotero_library_type'] == "":
            print("WARNING: Empty Zotero library type. Assuming to use your own Zotero library, not a shared group library.")
        library_type = config['zotero_library_type']
        library_id = config['zotero_library_id']
        api_key = config['zotero_api_key']
else:
    sys.exit("No config file found. Remember changing the name of config-sample.json to config.json")

def zotero_handle(msg):
    # Check for a valid telegram message of entity type 'url'.
    # This message gets parsed and is forwarded/saved to Zotero.
    if not (('chat' in msg) and (msg['chat']['type'] == 'channel') and (msg['chat']['title'] == CHAT_TITLE)):
        return "This chat message can not be saved to Zotero."

    if 'document' in msg:
        return "Can not add documents to Zotero."
    if 'text' not in msg:
        return "Can only add text of type 'url' to Zotero."

    #print("Chat Text: " + str(msg['text']))
    if 'entities' in msg:
        if 'type' in msg['entities'][0]:
            if msg['entities'][0]['type'] == "url":
                print("URL type -> Save to Zotero")
            else:
                print("No valid message to forward to Zotero")
    else:
        #print("No appropriate entity with type 'URL' found in message")
        #print("Cannot add to Zotero: Message is not of type 'url'")
        return "Cannot add to Zotero: Message is not of type 'url'"
    #print("Chat Entity Type: " + str(msg['entities'][0]['type'])) # must be url
    #print("Chat Entity Offset: " + str(msg['entities'][0]['offset']))
    #print("Chat Entity Length: " + str(msg['entities'][0]['length']))

    url_offset = msg['entities'][0]['offset']
    url_length = msg['entities'][0]['length']

    url = msg['text'][url_offset:]
    #print(url)
    if len(url) != url_length:
        print("URL length does not match")

    url_title = msg['text'][:url_offset]
    url_date = datetime.datetime.fromtimestamp(msg['date'])

    # "Allow write access" must be enabled to allow changes to your library
    # Prepare new Zotero object from template
    newItem = zot.item_template('blogPost')
    newItem['title'] = url_title
    newItem['url'] = url
    newItem['accessDate'] = url_date.strftime("%Y-%m-%d %H:%M:%S")
    newItem['tags'] = [{'tag': 'FromAndroid'}, {'tag': 'Unfiled'}]
    print([newItem])
    createdItem = zot.create_items([newItem])
    print(createdItem)
    # ToDo: Check for failures
    #
    #print(len(createdItem['failed']))
    #if createdItem
    if len(createdItem['failed']) != 0:
        zotero_msg = "Error " + str(createdItem['failed']['0']['code']) + " at attempt to write to Zotero: " + createdItem['failed']['0']['message']
        print(zotero_msg)
    elif len(createdItem['success']) != 0:
        zotero_msg = "Item " + str(createdItem['success']['0']) + " saved to Zotero."
        #print("Item " + str(createdItem['success']['0']) + " saved to Zotero.")
        print(zotero_msg)

    return zotero_msg


def get_url_from_msg(msg_chat_text):
    pass

def is_allowed(msg):
    if msg['chat']['type'] == 'channel':
        return True # all channel admins are allowed to use the bot (channels don't have sender info)
    return 'from' in msg and msg['from']['id'] in allowed

def handle(msg):
    print("Message: " + str(msg))
    # Handle message to save it to Zotero
    ret = zotero_handle(msg)
    # Add person as allowed
    content_type, chat_type, chat_id = telepot.glance(msg)

    # Let bot send message back to user
    bot.sendMessage(chat_id, ret)

    txt = ""
    if 'text' in msg:
        txt = txt + msg['text']
    elif 'caption' in msg:
        txt = txt + msg['caption']
    # Addme and rmme only valid on groups and personal chats.
    if msg['chat']['type'] != 'channel':
        if "/addme" == txt.strip()[:6]:
            if msg['chat']['type'] != 'private':
                bot.sendMessage(chat_id, "This command is meant to be used only on personal chats.")
            else:
                used_password = " ".join(txt.strip().split(" ")[1:])
                if used_password == PASSWORD:
                    allowed.add(msg['from']['id'])
                    save_allowed(allowed)
                    bot.sendMessage(chat_id, msg['from']['first_name'] + ", you have been registered " +
                                    "as an authorized user of this bot.")
                else:
                    bot.sendMessage(chat_id, "Wrong password.")
        if "/rmme" == txt.strip()[:5]:
            allowed.remove(msg['from']['id'])
            save_allowed(allowed)
            bot.sendMessage(chat_id, "Your permission for using the bot was removed successfully.")
    if is_allowed(msg):
        if txt != "":
            if "/add " == txt[:5]:
                txt_split = txt.strip().split(" ")
                if len(txt_split) == 2 and "#" == txt_split[1][0]:
                    tag = txt_split[1].lower()
                    name = ""
                    if msg['chat']['type'] == "private":
                        name = name + "Personal chat with " + msg['chat']['first_name'] + ((" " + msg['chat']['last_name']) if 'last_name' in msg['chat'] else "")
                    else:
                        name = msg['chat']['title']
                    chats[tag] = {'id': chat_id, 'name': name}
                    bot.sendMessage(chat_id, name + " added with tag " + tag)
                    save_status(chats)
                else:
                    bot.sendMessage(chat_id, "Incorrect format. It should be _/add #{tag}_", parse_mode="Markdown")
            elif "/rm " == txt[:4]:
                txt_split = txt.strip().split(" ")
                if len(txt_split) == 2 and "#" == txt_split[1][0]:
                    tag = txt_split[1].lower()
                    if tag in chats:
                        if chats[tag]['id'] == chat_id:
                            del chats[tag]
                            bot.sendMessage(chat_id, "Tag "+tag+" deleted from taglist.")
                            save_status(chats)
                            return
                        else:
                            bot.sendMessage(chat_id, "You can't delete a chat's tag from a different chat.")
                    else:
                        bot.sendMessage(chat_id, "Tag doesn't exist on TagList")
                else:
                    bot.sendMessage(chat_id, "Incorrect format. It should be _/rm #{tag}_", parse_mode="Markdown")

            elif "/taglist" ==  txt.strip()[:8]:
                tags_names = []
                for tag, chat in chats.items():
                    tags_names.append( (tag, chat['name']))
                response = "<b>TagList</b>"
                for (tag, name) in sorted(tags_names):
                    response = response + "\n<b>" + tag + "</b>: <i>" + name + "</i>"
                bot.sendMessage(chat_id, response, parse_mode="HTML")
            elif "#" == txt[0]:
                txt_split =txt.strip().split(" ")
                i = 0
                tags = []
                while i < len(txt_split) and txt_split[i][0] == "#":
                    tags.append(txt_split[i].lower())
                    i+=1
                if i != len(txt_split) or 'reply_to_message' in msg:
                    approved = []
                    rejected = []
                    for tag in tags:
                        if tag in chats:
                            if chats[tag]['id'] != chat_id:
                                approved.append(chats[tag]['name'])
                                bot.forwardMessage(chats[tag]['id'], chat_id, msg['message_id'])
                                if 'reply_to_message' in msg:
                                    bot.forwardMessage(chats[tag]['id'], chat_id, msg['reply_to_message']['message_id'])
                        else:
                            rejected.append(tag)
                    if len(rejected) > 0:
                        bot.sendMessage(chat_id, "Failed to send messages to tags <i>" + ", ".join(rejected) + "</i>", parse_mode="HTML")
                else:
                    bot.sendMessage(chat_id, "Failed to send a message only with tags which is not a reply to another message")

bot = telepot.Bot(TOKEN)
zot = zotero.Zotero(library_id, library_type, api_key)
zot.key_info() # Checks for successful permissions of Zotero instance.

MessageLoop(bot, handle).run_as_thread()
print('Listening ...')
# Keep the program running.
while 1:
    time.sleep(10)
