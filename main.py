import uuid
import telebot
from flask import Flask, request
import os
import requests
import json
import hmac
import hashlib
import logging

# Setup logging
logging.basicConfig(filename='bot_log.txt', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

TOKEN = '7137673728:AAE85wL1RBYskkrlCZaIzhEbgKmiEBiefDI'
APP_URL = f'https://youtubenew-c7c31f2cda46.herokuapp.com/{TOKEN}'
COINPAYMENTS_PUBLIC_KEY = '616e319dad674f8906f129a735d299d6665388a0fe3f4e075ffc3e2b9c3ce8f3'
COINPAYMENTS_PRIVATE_KEY = 'D544Edec2fa5725C5913C5806665393ec58769563f5C7477DfBb8A8C4302867b'
IPN_SECRET = '1122334455667788aA@'  # Replace with your CoinPayments IPN Secret

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# Dictionary to store user state (initiated payment or not)
user_states = {}


def generate_and_print_uuid():
    unique_id = uuid.uuid4()
    print(unique_id)

    unique_id_str = unique_id.hex
    print("UUID HEX:", unique_id_str)


def create_coinpayments_payment(amount, currency1, currency2, buyer_email, user_id):
    url = 'https://www.coinpayments.net/api.php'
    merchant_id = 'c80ec2928c4b6836e6ada19db1c229ec'

    payload = {
        'version': 1,
        'key': COINPAYMENTS_PUBLIC_KEY,
        'cmd': 'create_payment_button',  # Use create_payment_button for a custom button
        'amount': amount,
        'currency1': currency1,
        'currency2': currency2,
        'buyer_email': buyer_email,
        'success_url': APP_URL,
    }

    sorted_msg = '&'.join([f"{k}={v}" for k, v in payload.items()])
    digest = hmac.new(
        str(IPN_SECRET).encode(),
        f'{sorted_msg}'.encode(),
        hashlib.sha512
    )
    signature = digest.hexdigest()
    payload['hmac'] = signature
    payload['merchant'] = merchant_id

    try:
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

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return None


def get_tx_info(txn_id):
    url = 'https://www.coinpayments.net/api.php'

    payload = {
        'version': 1,
        'key': COINPAYMENTS_PUBLIC_KEY,
        'cmd': 'get_tx_info',
        'txid': txn_id,
    }

    sorted_msg = '&'.join([f"{k}={v}" for k, v in payload.items()])
    digest = hmac.new(
        str(IPN_SECRET).encode(),
        f'{sorted_msg}'.encode(),
        hashlib.sha512
    )
    signature = digest.hexdigest()
    payload['hmac'] = signature

    try:
        response = requests.post(url, data=payload)

        if response.status_code == 200:
            tx_info = response.json()
            return tx_info
        else:
            print(f"Error getting tx info: {response.status_code}, {response.text}")
            return None

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return None


def handle_callback_query(query):
    user_id = query.from_user.id
    data = query.data

    if data.startswith('ipn_'):
        txn_id = data[4:]
        tx_info = get_tx_info(txn_id)

        if tx_info:
            # Check the payment status and update user state
            # Inform the user about the payment status
            pass
        else:
            logging.error(f"Error getting tx info for txn_id: {txn_id}")

    else:
        logging.error(f"Unknown callback data: {data}")


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_states[user_id] = 'initiated'

    try:
        payment_link = create_coinpayments_payment(amount=25, currency1='usd', currency2='btc', buyer_email='buyer@example.com', user_id=user_id)
    except Exception as e:
        logging.error(f"An error occurred while creating payment link: {str(e)}")
        bot.send_message(user_id, 'Error creating payment link. Please try again later.')
        return

    if payment_link:
        bot.send_message(user_id, f'Click the link below to make a payment:\n{payment_link}')
    else:
        bot.send_message(user_id, 'Error creating payment link. Please try again later.')


@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo(message):
    user_id = message.from_user.id
    if user_states.get(user_id) == 'initiated':
        bot.send_message(user_id, 'Checking payment status...')
        # Implement logic to check payment status using get_tx_info or IPN (refer to CoinPayments documentation)
        # Update user state and inform them about the payment status
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
