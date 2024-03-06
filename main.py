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

def generate_and_print_uuid():
    unique_id = uuid.uuid4()
    print(unique_id)

    unique_id_str = unique_id.hex
    print("UUID HEX:", unique_id_str)

def verify_coinpayments_ipn(ipn_data):
    merchant_id = 'c80ec2928c4b6836e6ada19db1c229ec'
    ipn_secret = '1122334455667788aA@'

    if 'merchant' not in ipn_data or 'ipn_type' not in ipn_data:
        return False

    if ipn_data['merchant'] != merchant_id:
        return False

    ipn_type = ipn_data['ipn_type']
    ipn_mode = ipn_data.get('ipn_mode', 'hmac')

    if ipn_type == 'api' and ipn_mode == 'hmac':
        ipn_id = ipn_data.get('ipn_id', '')
        ipn_txn_id = ipn_data.get('txn_id', '')
        ipn_status = ipn_data.get('status', '')
        ipn_status_text = ipn_data.get('status_text', '')

        hmac_signature = ipn_data.get('hmac', '')
        sorted_msg = '&'.join([f"{k}={v}" for k, v in sorted(ipn_data.items())])
        digest = hmac.new(
            str(ipn_secret).encode(),
            f'{sorted_msg}'.encode(),
            hashlib.sha512
        )
        calculated_hmac = digest.hexdigest()

        if calculated_hmac == hmac_signature:
            return True
        else:
            return False

    return False

def create_coinpayments_payment(buyer_email):
    url = 'https://www.coinpayments.net/api.php'

    payload = {
        'version': 1,
        'key': COINPAYMENTS_PUBLIC_KEY,
        'cmd': 'create_transaction',
        'amount': 25,  # مبلغ ثابت 25 دلار
        'currency1': 'usd',
        'currency2': 'btc',
        'buyer_email': buyer_email,
        'success_url': APP_URL,
    }

    sorted_msg = '&'.join([f"{k}={v}" for k, v in payload.items()])
    digest = hmac.new(
        str(COINPAYMENTS_PRIVATE_KEY).encode(),
        f'{sorted_msg}'.encode(),
        hashlib.sha512
    )
    signature = digest.hexdigest()
    payload['hmac'] = signature

    response = requests.post(url, data=payload)

    if response.status_code == 200:
        payment_data = response.json()
        checkout_url = payment_data.get('result', {}).get('checkout_url')
        return checkout_url
    else:
        print(f"Error creating payment link: {response.status_code}, {response.text}")
        return None


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    payment_link = create_coinpayments_payment(buyer_email='buyer@example.com')

    if payment_link:
        bot.send_message(user_id, f'Click the link below to make a payment:\n{payment_link}')
    else:
        bot.send_message(user_id, 'Error creating payment link. Please try again later.')

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
    generate_and_print_uuid()
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
