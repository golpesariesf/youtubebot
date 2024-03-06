import uuid
import telebot
from flask import Flask, request
import os
import requests
import json
import hmac
import hashlib

TOKEN = '7137673728:AAE85wL1RBYskkrlCZaIzhEbgKmiEBiefDI'
APP_URL = f'https://youtubenew-c7c31f2cda46.herokuapp.com/{TOKEN}'
NOWPAYMENTS_API_KEY = '4H1ZFMD-459MGM6-HFX476C-VHB4A66'
NOWPAYMENTS_SECRET_KEY = 'gcCRjKMtHxG3VHNAGbF65q8MmFfJ1U+1'

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

def generate_and_print_uuid():
    unique_id = uuid.uuid4()
    print(unique_id)

    unique_id_str = unique_id.hex
    print("UUID HEX:", unique_id_str)

def create_nowpayments_payment_link(amount, currency):
    url = 'https://api.nowpayments.io/v1/payment'
    headers = {
        'x-api-key': NOWPAYMENTS_API_KEY,
        'Content-Type': 'application/json',
    }

    payload = {
        'price_amount': amount,
        'price_currency': currency,
        'pay_currency': currency,  # You can change this to the desired payment currency
        'order_id': str(uuid.uuid4()),  # Generate a unique order ID
    }

    sorted_msg = json.dumps(payload, separators=(',', ':'), sort_keys=True)
    digest = hmac.new(
        str(NOWPAYMENTS_SECRET_KEY).encode(),
        f'{sorted_msg}'.encode(),
        hashlib.sha512
    )
    signature = digest.hexdigest()
    headers['x-signature'] = signature

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        payment_data = response.json()
        payment_link = payment_data.get('payment_url')
        return payment_link
    else:
        print(f"Error creating payment link: {response.status_code}, {response.text}")
        return None

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    payment_link = create_nowpayments_payment_link(amount=25, currency='usd')

    if payment_link:
        bot.send_message(user_id, f'Click the link below to make a payment:\n{payment_link}')
    else:
        bot.send_message(user_id, 'Error creating payment link. Please try again later.')

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
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
