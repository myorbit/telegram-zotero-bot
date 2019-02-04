# telegram-zotero-bot

A simple Telegram bot that can be used to share a webpage and forward it to Zotero.

Create a private Telegram channel and specify your credentials in the file config.json. Add your Zotero credentials as well and in the Zotero settings enable **"Allow write access"** to allow changes to your library.

## Required Python packages

Tested with Python 3.6 and 3.7 and requires the following packages:

* telepot
* Pyzotero

See also Pipfile for details.

---
This bot was inspired by [telegram-forward-bot](https://github.com/adderou/telegram-forward-bot).
