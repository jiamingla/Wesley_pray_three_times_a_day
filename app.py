from __future__ import unicode_literals
import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from bs4 import BeautifulSoup
from datetime import date, datetime

import requests

import configparser

import random

import json

app = Flask(__name__)

# LINE 聊天機器人的基本資料
config = configparser.ConfigParser()
config.read('config.ini')

line_bot_api = LineBotApi(config.get('line-bot', 'channel_access_token'))
handler = WebhookHandler(config.get('line-bot', 'channel_secret'))


# 接收 LINE 的資訊
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    
    try:
        print(body, signature)
        handler.handle(body, signature)
        
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# 當有人傳訊息給我的時候會觸發這個
@handler.add(MessageEvent, message=TextMessage)
def get_info_today(event):
    today = datetime.today().strftime("%Y-%m-%d")
    with open('today_data.json', 'r+', encoding='utf8', newline='', closefd=True) as jsonfile:
        data = json.load(jsonfile)
        if(data["date"] != today):
            r = requests.get(f'https://methodist.org.tw/{today}/')
            soup = BeautifulSoup(r.text, 'html.parser')
            info = soup.find("div", class_ = "column_attr clearfix")
            info_contents = info.stripped_strings
            pray_morning = []
            pray_noon = []
            pray_afternoon = []
            split_count = 0
            author = ""
            for index, value in enumerate(info_contents,0):
                if(index == 0):
                    author = value
                    continue
                pray_morning.append(value)
                if("影音" in value):
                    split_count = index
                    break
            for index, value in enumerate(info_contents,split_count):
                pray_noon.append(value)
                if("影音" in value):
                    split_count = index
                    break
            for index, value in enumerate(info_contents,split_count):
                pray_afternoon.append(value)
                if("影音" in value):
                    split_count = index
                    break

            def transfer_lict_to_string(string_list: list):
                string = ""
                for e in string_list:
                    string = string + e + "\n"
                return string
            string_morning = transfer_lict_to_string(pray_morning)
            string_noon = transfer_lict_to_string(pray_noon)
            string_afternoon = transfer_lict_to_string(pray_afternoon)

            pray_youtube_url = info.find_all("iframe")
            pray_morning_youtube_url = pray_youtube_url[0].get('src')
            pray_noon_youtube_url = pray_youtube_url[1].get('src')
            pray_afternoon_youtube_url = pray_youtube_url[2].get('src')

            data = {"date":today,"author":author,
                    "morning_story":string_morning,"morning_youtube":pray_morning_youtube_url,
                    "noon_story":string_noon,"noon_youtube":pray_noon_youtube_url,
                    "afternoon_story":string_afternoon,"afternoon_youtube":pray_afternoon_youtube_url,
                    }
            json.dump(data, jsonfile, indent=4, ensure_ascii=False)
    string = ""
    for e in data:
        string = string + str(e) + "\n"
    line_bot_api.reply_message(
    event.reply_token,
    TextSendMessage(text=string)
    )

if __name__ == "__main__":
    app.run()