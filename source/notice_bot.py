#!/usr/bin/python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import sqlite3
import telegram
import time

from telegram.ext import Updater
from telegram.ext import Dispatcher
from telegram.ext import CommandHandler

import signal, os
import os.path
import logging

# Database Diagram
# CREATE TABLE announce (
#     title TEXT NOT NULL,
#     url TEXT NOT NULL,
#     writer TEXT NOT NULL,
#     date TEXT NOT NULL,
#     atype TEXT NOT NULL
# );

# Execution Example
# conn.execute("INSERT INTO COMPANY (ID,NAME,AGE,ADDRESS,SALARY) VALUES (1, 'Paul', 32, 'California', 20000.00 )");

URL_1 = 'http://computer.knu.ac.kr/06_sub/02_sub.html'
URL_2 = 'http://computer.knu.ac.kr/06_sub/02_sub_2.html'
URL_3 = 'http://computer.knu.ac.kr/06_sub/02_sub_3.html'
URL_4 = 'http://computer.knu.ac.kr/06_sub/02_sub_4.html'
URL_5 = 'http://computer.knu.ac.kr/06_sub/02_sub_6.html'

announcement_type = ""
announcement_writer = ""
announcement_date = ""
announcement_url = ""
announcement_title = ""


# read token from file
def get_token():
	BASE_DIR = os.path.dirname(os.path.abspath(__file__))
	TOKEN = os.path.join(BASE_DIR, 'token.txt')
	f = open(TOKEN, "r")
	token = f.read()
	token.rstrip()
	f.close()
	return token


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="This is announcement bot KNU computer science department!")
    context.bot.send_message(chat_id=update.effective_chat.id, text="I will let you know when there's new announcement!")
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="You can cancel subscription by typing \"/leave\" whenever you want")
    add_user(update.effective_chat.id)
    print(update.effective_chat.id)


def add_user(user):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    USER = os.path.join(BASE_DIR, 'user.txt')
    f = open(USER, "a+")
    f.write(str(user) + "\n")
    f.close()


def leave(update, context):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    USER = os.path.join(BASE_DIR, 'user.txt')
    user_id = update.effective_chat.id
    f = open(USER, "r")
    lines = f.readlines()
    f.close()

    f = open(USER, "w")
    for line in lines:
        if line.strip('\n') != str(user_id):
            f.write(line)
    f.close()

def RepresentsInt(s):
    try:
        int(s)
        return 1
    except ValueError:
        return 0


def get_announcement_feed(URL, conn, cur, selected):
    global announcement_title
    global announcement_writer
    global announcement_date
    global announcement_url
    global announcement_title
    global announcement_type
    global bot

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    USER = os.path.join(BASE_DIR, 'user.txt')

    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    tr = soup.findAll('table')[0].findAll('tr')

    for announcement in tr[1:]:
        time.sleep(1)
        bbs_num = str(announcement.find_all(attrs={'class': 'bbs_num'}))
        bbs_num = bbs_num.replace("</th>]", "")
        bbs_num = bbs_num.replace("</td>]", "")
        bbs_num = bbs_num.replace('[<th class="bbs_num">', "")
        bbs_num = bbs_num.replace('[<td class="bbs_num">', '')
        announcement_type = str(RepresentsInt(bbs_num))

        print(announcement_type)

        # bbs_writer
        bbs_writer = str(announcement.find_all(attrs={'class': 'bbs_writer'}))
        bbs_writer = bbs_writer.replace("</td>]", "")
        bbs_writer = bbs_writer.replace('[<td class="bbs_writer">', '')
        announcement_writer = str(bbs_writer)
        print(announcement_writer)

        # bbs_date
        bbs_date = str(announcement.find_all(attrs={'class': 'bbs_date'}))
        bbs_date = bbs_date.replace("</td>]", "")
        bbs_date = bbs_date.replace('[<td class="bbs_date">', '')
        announcement_date = str(bbs_date)
        print(announcement_date)

        # announcement_url and announcement_title
        for a in announcement.find_all('a', href=True):
            announce_url = str(a["href"])
            announcement_url = URL + announce_url
            announcement_title = str(a["title"]).replace("'", " ")

        print(announcement_url)
        print(announcement_title)

        # Initializing DB
        if insert_announcement_record(conn, cur, announcement_title, announcement_url, announcement_writer, announcement_date, announcement_type):
            message_query = selected + ": \n" + "제목: " + announcement_title + "\n작성자: " + announcement_writer + "\n링크: " + announcement_url + "\n날짜: " + announcement_date

            f = open(USER, "r")
            users = f.readlines()
            f.close()

            for user in users:
                try:
                    # send message
                    bot.send_message(chat_id=user.strip('\n'), text=message_query)
                except:
                    # remove user if error while sending message
                    f = open(USER, "r")
                    lines = f.readlines()
                    f.close()

                    f = open(USER, "w")
                    for line in lines:
                        if line.strip("\n") != user.strip("\n"):
                            f.write(line)
                    f.close()

                    print("deleted user {}".format(user))

                time.sleep(1)


def connect_sqlite3(db_name):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, db_name)
    conn = sqlite3.connect(db_path)
    print("Opened database successfully")
    cur = conn.cursor()
    return conn, cur


def insert_announcement_record(conn, cur, announcement_title, announcement_url, announcement_writer, announcement_date, announcement_type):
    if select_announcement_from_table(cur):
        return 0
    else:
        query = "INSERT INTO announce (title, url, writer, date, atype) VALUES ('" + announcement_title + "', '" + announcement_url + "', '" + announcement_writer + "', '" + announcement_date + "', '" + announcement_type + "')"
        cur.execute(query)
        conn.commit()
        return 1


def select_announcement_from_table(cur):
    cur.execute("SELECT * FROM announce WHERE title IS '" + announcement_title + "'")
    rows = cur.fetchone()
    if rows:
        return 1
    else:
        return 0


def clean_up(conn, cur):
    cur.close()
    conn.close()


if __name__ == "__main__":
    TOKEN = ''
    # telegram bot related information
    bot = telegram.Bot(token=TOKEN)
	

    # Initializing the DB
    conn, cur = connect_sqlite3("announcement.db")

    updater = Updater(token=TOKEN, use_context=True, request_kwargs={'read_timeout': 6, 'connect_timeout': 7})
    dispatcher = updater.dispatcher

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    start_handler = CommandHandler('start', start)
    leave_handler = CommandHandler('leave', leave)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(leave_handler)
    updater.start_polling()

    while True:
        get_announcement_feed(URL_1, conn, cur, '전체 공지')
        get_announcement_feed(URL_2, conn, cur, '학사 공지')
        get_announcement_feed(URL_3, conn, cur, '심컴')
        get_announcement_feed(URL_4, conn, cur, '글솝')
        get_announcement_feed(URL_5, conn, cur, '대학원')
        print("waiting for 1800 seconds")
        time.sleep(1800)
    clean_up(conn, cur)


