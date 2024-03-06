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
COINPAYMENTS_PUBLIC_KEY = '616e319dad674f8906f129a735d299d6665388a0fe3f4e075ffc3e2b9c3ce8f3'
COINPAYMENTS_PRIVATE_KEY = 'D544Edec2fa5725C5913C5806665393ec58769563f5C7477DfBb8A8C4302867b'

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# Dictionary to store user state (whether they have initiated the payment or not)
user_states = {}

def generate_and_print_uuid():
    unique_id = uuid.uuid4()
    print(unique_id)

    unique_id_str = unique_id.hex
    print("UUID HEX:", unique_id_str)

def create_coinpayments_payment(amount, currency1, currency2, buyer_email, user_id):
    url = 'https://www.coinpayments.net/api.php'
    merchant_id = 'c80ec2928c4b6836e6ada19db1c229ec'
    ipn_secret = '1122334455667788aA@'

    payload = {
        'version': 1,
        'key': COINPAYMENTS_PUBLIC_KEY,
        'cmd': 'create_transaction',
        'amount': amount,
        'currency1': currency1,
        'currency2': currency2,
        'buyer_email': buyer_email,
        'success_url': APP_URL,
    }

    sorted_msg = '&'.join([f"{k}={v}" for k, v in payload.items()])
    digest = hmac.new(
        str(ipn_secret).encode(),
        f'{sorted_msg}'.encode(),
        hashlib.sha512
    )
    signature = digest.hexdigest()
    payload['hmac'] = signature
    payload['merchant'] = merchant_id

    response = requests.post(url, data=payload)

    if response.status_code == 200:
        payment_data = response.json()
        checkout_url = payment_data.get('result', {}).get('checkout_url')

        if checkout_url:
            return checkout_url
        else:
            print(f"Error creating payment link: {response.status_code}, {response.text}")
            return None
    else:
        print(f"Error creating payment link: {response.status_code}, {response.text}")
        return None

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_states[user_id] = 'initiated'
    payment_link = create_coinpayments_payment(amount=25, currency1='usd', currency2='btc', buyer_email='buyer@example.com', user_id=user_id)

    if payment_link:
        bot.send_message(user_id, f'Click the link below to make a payment:\n{payment_link}')
    else:
        bot.send_message(user_id, 'Error creating payment link. Please try again later.')

@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo(message):
    user_id = message.from_user.id
    if user_states.get(user_id) == 'initiated':
        bot.send_message(user_id, 'You have initiated the payment. Please proceed with the payment.')
    else:
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
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8090)))
