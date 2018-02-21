from bs4 import BeautifulSoup
from requests import get
import telegram
from telegram.ext import Updater, CommandHandler, InlineQueryHandler
import random
import re
from uuid import uuid4
from telegram.utils.helpers import escape_markdown
from telegram import InlineQueryResultArticle, ParseMode, InputTextMessageContent
import numpy as np


bot_token = "493594627:AAEa7D96j6fCsvl_N1qJOnV25DuYp03Nsn4"


def make_soup(url):
    page = get(url)
    if page.status_code != 200:
        return None
    return BeautifulSoup(page.text, "html.parser")


def sanitize_query(args):
    # sanitizes query
    query = " ".join(args)
    non_alpha = re.compile("[\W_]+", re.UNICODE)
    return non_alpha.sub(" ", query).strip()


def giffetteria(bot, update, args):
    # get args from message
    if args:
        query = sanitize_query(args)
    else:
        query = ""
    print(query)
    url = "http://giffetteria.it/?s="
    soup = make_soup(url + query)
    # get all gif links from page
    gif_urls = []
    for gif_link in soup.find_all("img", attrs={"class": "gl-lazy"}):
        gif_urls.append(gif_link.get("data-gif"))
    try:
        random_gif = random.choice(gif_urls)
    except:
        random_gif = "http://giffetteria.it/archivio/signoresignori13.gif"
        bot.send_message(chat_id=update.message.chat_id,
                     text="Nessuna GIF trovata in archivio, prova con un'altra parola chiave...", parse_mode="markdown")
    bot.send_document(chat_id=update.message.chat_id, document=random_gif)


def inlinequery(bot, update):
    """Handle the inline query. And looks for gifs"""
    # TO DO
    # DOESN'T READ INLINE QUERY
    query = update.inline_query.query
    print(query)
    url = "http://giffetteria.it/?s="
    soup = make_soup(url + query)
    # get all gif links from page
    gif_urls = []
    gif_thumbs = []
    for gif_link in soup.find_all("img", attrs={"class": "gl-lazy"}):
        gif_urls.append(gif_link.get("data-gif"))
        gif_thumbs.append(gif_link.get("data-thumb"))
    gifs = np.array([gif_urls, gif_thumbs])
    # send gifs to inline results
    results = [InlineQueryResultArticle(
               id=uuid4(),
               gif_url=gifs[0,i],
               thumb_url=gifs[1,i]) for i in range(gifs.shape[1])]
    print(gifs)
    update.inline_query.answer(results)


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="`/giffetteria` query", parse_mode="markdown")


update = Updater(token=bot_token)
dp = update.dispatcher
dp.add_handler(CommandHandler('giffetteria', giffetteria, pass_args=True))
dp.add_handler(CommandHandler(["start", "help", "aiuto"], start))
dp.add_handler(InlineQueryHandler(inlinequery))
update.start_polling()
update.idle()
