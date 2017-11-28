from bs4 import BeautifulSoup
from requests import get
from telegram.ext import Updater, CommandHandler
import json
import urllib.request
import random
import re


bot_token = ""


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
    # finds article uuid and passes to apicommunity
    gazz_uuid = soup.find("div", attrs={"id": "uuid-article"})["data-cmsid"]
    with urllib.request.urlopen("http://apicommunity.gazzetta.it/api/getComments/uuid_" + gazz_uuid) as url:
        return json.loads(url.read().decode())


# parse votes from json as it doesn't store all the values all the time
def parse_votes(comment_dict):
    if comment_dict["votes"]:
        votes = [0, 0]
        for vote in comment_dict["votes"]:
            if vote["type"] == "like":
                votes[0] += int(vote["count"])
            else:
                votes[1] += int(vote["count"])
        return "`+{0:d}|-{1:d}`".format(votes[0], votes[1])
    else:
        return "`+0|-0`"


def parse_comment(c, query):
    votes = parse_votes(c)
    return "👤 *{1:s}* {2:s}\n_RE: {0:s}_\n\n{3:s}".format(query, c["author_name"], votes, c["content"].replace("<br>", " "))


def json_to_dict(user_comment):
    json_dict = {}
    json_dict["author_name"] = user_comment.get("author_name")
    json_dict["content"] = user_comment.get("content")
    json_dict["votes"] = user_comment.get("votes")
    json_dict["thread_votes_count"] = user_comment.get("thread_votes_count")
    return json_dict

# creates list with all comments


def merge_parents_children(json):
    parents_children = []
    for parent in json:
        parents_children.append(json_to_dict(parent))
        if parent["children"]:
            for child in parent["children"]:
                parents_children.append(json_to_dict(child))
    return parents_children


def make_string(comments_json, like, query):
    all_comments = merge_parents_children(comments_json)
    while True:
        # take random comment
        temp_comm = random.choice(all_comments)
        # /commento
        if like == 0:
            string = parse_comment(temp_comm, query)
            break
        # /positivo
        elif like == 1 and int(temp_comm["thread_votes_count"]) >= 0:
            string = parse_comment(temp_comm, query)
            break
        # /negativo
        elif like == 2 and int(temp_comm["thread_votes_count"]) < 0:
            string = parse_comment(temp_comm, query)
            break
    return string


def get_comment(link, like, query):
    # grabs article page
    soup = make_soup(link)
    if soup is None:
        return False
    else:
        comments_json = get_json_comm(soup)
        if comments_json:
            string = make_string(comments_json, like, query)
        else:
            return False
        return string


def main(bot, update, args, like):
    # sanitizes query
    query = " ".join(args)
    non_alpha = re.compile("[\W_]+", re.UNICODE)
    query = non_alpha.sub(" ", query).strip()
    # gets links from search page
    links = get_articles_url(
        make_soup("http://sitesearch.gazzetta.it/sitesearch/home.html?q=" + query))
    # tries to find a comment
    while True:
        link = random.choice(links)
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
updater.dispatcher.add_handler(CommandHandler(
    'commento', commento, pass_args=True))
updater.dispatcher.add_handler(
    CommandHandler('positivo', like, pass_args=True))
updater.dispatcher.add_handler(
    CommandHandler('negativo', dislike, pass_args=True))
updater.dispatcher.add_handler(
    CommandHandler(["start", "help", "aiuto"], start))
updater.start_polling()
updater.idle()
