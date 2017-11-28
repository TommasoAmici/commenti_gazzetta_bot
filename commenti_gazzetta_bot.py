from bs4 import BeautifulSoup
from requests import get
from telegram.ext import Updater, CommandHandler
import json
import urllib.request
import random

bot_token =


def make_soup(url):
    page = get(url)
    if page.status_code != 200:
        return None
    return BeautifulSoup(page.text, "html.parser")


def get_articles_url(soup):
    urls = []
    for article in soup.find_all("article", attrs={"class": "u024-article odd"}):
        urls.append(article.find("a").get("href"))
    return urls


def get_json_comm(soup):
    gazz_uuid = soup.find("div", attrs={"id": "uuid-article"})["data-cmsid"]
    with urllib.request.urlopen("http://apicommunity.gazzetta.it/api/getComments/uuid_" + gazz_uuid) as url:
        return json.loads(url.read().decode())


def parse_comment(c, query):
    if c["votes"]:
        return "👤 *{1:s}* `+{2:s}|-{3:s}`\n_RE: {0:s}_\n\n{4:s}".format(query, c["author_name"], c["votes"][0]["count"], c["votes"][1]["count"], c["content"].replace("<br>", " "))
    else:
        return "👤 *{1:s}* `0|0`\n_RE: {0:s}_\n\n{2:s}".format(query, c["author_name"], c["content"].replace("<br>", " "))


def get_comment(link, like, query):
    # grabs article page
    soup = make_soup(link)
    if soup is None:
        return False
    else:
        # finds article uuid and passes to apicommunity
        comments_json = get_json_comm(soup)
        while True:
            temp_comm = random.choice(comments_json)
            if like == 0:
                string = parse_comment(temp_comm, query)
                break
            elif like == 1 and int(temp_comm["thread_votes_count"]) >= 0:
                string = parse_comment(temp_comm, query)
                break
            elif like == 2 and int(temp_comm["thread_votes_count"]) < 0:
                string = parse_comment(temp_comm, query)
                break
        return string


def main(bot, update, args, like):
    query = " ".join(args)
    non_alpha = re.compile("[\W_]+", re.UNICODE)
    query = non_alpha.sub(" ", query).strip()
    links = get_articles_url(make_soup("http://sitesearch.gazzetta.it/sitesearch/home.html?q=" + query))
    for link in links:
        string = get_comment(link, like, query)
        if string:
            break
    bot.send_message(chat_id=update.message.chat_id,
                     text=string,
                     parse_mode="markdown")
    return


def like(bot, update, args):
    like = 1
    main(bot, update, args, like)
    return


def dislike(bot, update, args):
    like = 2
    main(bot, update, args, like)
    return


def commento(bot, update, args):
    like = 0
    main(bot, update, args, like)
    return


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="`/commento [query]` per un commento a caso\n`/positivo [query]` per un commento con voto positivo\n`/negativo [query]` per un commento con voto negativo", parse_mode="markdown")


updater = Updater(bot_token)
updater.dispatcher.add_handler(CommandHandler('commento', commento, pass_args=True))
updater.dispatcher.add_handler(CommandHandler('positivo', like, pass_args=True))
updater.dispatcher.add_handler(CommandHandler('negativo', dislike, pass_args=True))
updater.dispatcher.add_handler(CommandHandler(["start", "help", "aiuto"], start))
updater.start_polling()
updater.idle()
