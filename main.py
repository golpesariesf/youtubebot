import uuid
import telebot
from flask import Flask, request
import os

TOKEN = '7095077129:AAE-rDWtk6q7S8ZgkxmcfLtnJdMtAYJutq4'
APP_URL = f'https://youtubenew-c7c31f2cda46.herokuapp.com/{TOKEN}'
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

def generate_and_print_uuid():
    unique_id = uuid.uuid4()
    print(unique_id)

    unique_id_str = unique_id.hex
    print("UUID HEX:", unique_id_str)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 'Hello, ' + message.from_user.first_name)
    generate_and_print_uuid()

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
