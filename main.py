﻿import uuid
import telebot
from flask import Flask, request
import os

TOKEN = '7095077129:AAE-rDWtk6q7S8ZgkxmcfLtnJdMtAYJutq4'
APP_URL = f'https://youtubenew-c7c31f2cda46.herokuapp.com/{TOKEN}'
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# Setup logging ggggg
logging.basicConfig(filename='bot_log.txt', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def generate_and_print_uuid():
    unique_id = uuid.uuid4()
    print(unique_id)

    unique_id_str = unique_id.hex
    print("UUID HEX:", unique_id_str)

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    # Create an inline keyboard with a link button
    markup = types.InlineKeyboardMarkup()
    link_button = types.InlineKeyboardButton("Click here to pay", url=f'https://www.coinpayments.net/index.php?cmd=_pay&reset=1&merchant=c80ec2928c4b6836e6ada19db1c229ec&item_name=iphone15&currency=USD&amountf=25.00000000&quantity=1&allow_quantity=0&want_shipping=0&allow_extra=1&')
    markup.add(link_button)

    bot.reply_to(message, "To make a payment, click on the button below:", reply_markup=markup)

@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo(message):
    bot.reply_to(message, message.text)

@server.route('/' + TOKEN, methods=['POST'])
def get_message():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '!', 200

@server.route('/')
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    return '!', 200

if __name__ == '__main__':
    generate_and_print_uuid()  # Add this line if you want to print a UUID when the script is run
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
