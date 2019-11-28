from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from beem import Steem
from beem.account import Account
from beem.comment import Comment
from beem.nodelist import NodeList
from steemengine.api import Api
from steemengine.wallet import Wallet
from steemengine.tokens import Tokens
from steemengine.tokenobject import Token
from steemengine.market import Market
import time
import random
import schedule
import json
from dhooks import Webhook
import math
from beem.nodelist import NodeList
import json
import six
import requests
import getpass

beem_pass = "" # Password to unlock beem wallet

api = Api()
tokens = Tokens()
token = Token("TMPS")
stm = Steem()
market = Market(steem_instance=stm)
wallet = Wallet("tmps", steem_instance=stm)
wallet2 = Wallet("market", steem_instance=stm)
stm.wallet.unlock(pwd=beem_pass)
blacklist = ["market", "tokens", "null", "tmps"]
dragon_token = wallet.get_token("TMPS")
wallet.refresh()
upvote_account = "ufm.pay"
adjusted_dragon = float(dragon_token["balance"]) * 0.95
balances = token.get_holder()
info = token.get_info()
max_post_age_days = 6
min_post_age = 5
whitelist = []
blacklist_tags = []
only_main_posts = True
sell_tokens = ["SPORTS", "NEOXAG", "PHOTO", "PAL"]

def seller():
    print("started selling")
    markets = market.get_metrics()
    for m in markets:
        if m["symbol"] in sell_tokens:
            symbol = m["symbol"]
            sell_balance = wallet.get_token(symbol)
            bal = sell_balance["balance"]
            print(bal + m["symbol"])
            if float(bal) < 0.0000001:
                continue
            price = float(m["highestBid"])
            stm.wallet.unlock(pwd=beem_pass)
            print(market.sell("tmps", bal, m["symbol"], price))
            time.sleep(3)



def votecall():
    for b in balances:
        if len(blacklist) > 0 and b["account"] in blacklist:
            print("blacklisted user, skipping...")
            continue
        if float(b["balance"]) < 5:
            print("user under minimum balance")
            continue
        account = Account(b["account"])
        for post in account.get_blog(limit=1):
            c = Comment(post, steem_instance=stm)
            if (c.time_elapsed().total_seconds() / 60 / 60 / 24) > max_post_age_days:
                print("Post is to old, skipping")
                time.sleep(1)
                continue
            if (c.time_elapsed().total_seconds() / 60) < min_post_age:
                print("Post is to new, skipping")
                time.sleep(1)
                continue
            tags_ok = True
            if len(blacklist_tags) > 0 and "tags" in c:
                for t in blacklist_tags:
                    if t in c["tags"]:
                        tags_ok = False
            if not tags_ok:
                print("skipping, as one tag is blacklisted")
                time.sleep(1)
                continue
            already_voted = False
            for v in c["active_votes"]:
                if v["voter"] == upvote_account:
                    already_voted = True
            if already_voted:
                print("skipping, as already upvoted")
                continue
            upvote_weight = float(b["balance"]) / 20
            if c["author"] != b["account"]:
                print("Skipping reblog")
                continue
            if upvote_weight > 100:
                upvote_weight = 100
                print("upvote %s from %s with %.2f %%" % (c["permlink"], c["author"], upvote_weight))
                c.upvote(weight=upvote_weight, voter=upvote_account)
                time.sleep(3)
                reply_body = "You have received a " + str(upvote_weight) + "% upvote based on your balance of " + str(
                    b["stake"]) + " TMPS!"
                c.reply(body=reply_body, author=upvote_account)
                print("sending comment")
                time.sleep(1)
                continue
            print("upvote %s from %s with %.2f %%" % (c["permlink"], c["author"], upvote_weight))
            c.upvote(weight=upvote_weight, voter=upvote_account)
            time.sleep(3)
            reply_body = "You have received a " + str(upvote_weight) + "% upvote based on your balance of " + str(
                b["balance"]) + " TMPS!"
            c.reply(body=reply_body, author=upvote_account)
            print("sending comment")
            time.sleep(1)
    print("Process Complete!")
    time.sleep(5)

def tmps_payouts():
    wallet.refresh()
    balances = token.get_holder()
    info = token.get_info()
    sellbook = market.get_sell_book("TMPS")
    market_total = 0
    for s in sellbook:
        market_total = float(market_total) + float(s["quantity"])
    for b in balances:
        real_supply = float(info["circulatingSupply"]) - float(market_total)
        stake_share = float(b["balance"]) / float(real_supply)
        steem_balance = wallet.get_token("STEEMp")
        final = float(steem_balance["balance"]) * float(stake_share)
        if len(blacklist) > 0 and b["account"] in blacklist:
            print("blacklisted user, skipping...")
            continue
        if float(final) < 0.00000001:
            print(b["account"] + " under minimum stake with balance of " + b["balance"])
            continue
        stm.wallet.unlock(pwd=beem_pass)
        print(wallet.transfer(b["account"], final, "STEEMp", "Testing TMPS payouts!"))
        time.sleep(5)
    print("Process Complete!")
    time.sleep(5)

schedule.every(5).minutes.do(votecall)
schedule.every().friday.at("00:00").do(tmps_payouts)
schedule.every().day.at("23:45").do(seller)

while True:
    # Checks whether a scheduled task
    # is pending to run or not
    schedule.run_pending()
    time.sleep(1)
