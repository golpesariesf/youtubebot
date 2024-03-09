import os
from flask import Flask, request
import json
import hmac
import hashlib
import logging
import requests
import uuid
from coinpayments import CoinPaymentsAPI
import telebot

logging.basicConfig(filename='bot_log.txt', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

TOKEN = '7095077129:AAE-rDWtk6q7S8ZgkxmcfLtnJdMtAYJutq4'
APP_URL = f'https://youtubenew-c7c31f2cda46.herokuapp.com/{TOKEN}'
COINPAYMENTS_PUBLIC_KEY = '616e319dad674f8906f129a735d299d6665388a0fe3f4e075ffc3e2b9c3ce8f3'
COINPAYMENTS_PRIVATE_KEY = 'D544Edec2fa5725C5913C5806665393ec58769563f5C7477DfBb8A8C4302867b'
IPN_SECRET = '1122334455667788aA@'  # Replace with your CoinPayments IPN Secret
MERCHANT_ID = "c80ec2928c4b6836e6ada19db1c229ec"  # Add your own

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)
api = CoinPaymentsAPI(public_key=COINPAYMENTS_PUBLIC_KEY, private_key=COINPAYMENTS_PRIVATE_KEY)

@server.route('/ipn', methods=['POST'])
def handle_ipn():
    ipn = request.get_json()
    if not ipn:
        return 'Invalid IPN', 400

    if not api.verify_ipn(ipn, IPN_SECRET):
        return 'Invalid IPN', 400

    tx_info = api.get_tx_info(ipn['txn_id'])
    if tx_info['status'] == 100:
        print('پرداخت کامل شده است')
    elif tx_info['status'] < 0:
        print('پرداخت ناموفق بود')
    else:
        print('پرداخت در حال پردازش است')

    return 'OK'

@server.route('/webhook', methods=['POST'])
def handle_telegram_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    return 'Webhook set successfully!', 200

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    txn_id = message.text

    if not txn_id or len(txn_id) != 32:
        bot.send_message(user_id, "شناسه تراکنش نامعتبر است.")
        return

    payment_link = "https://www.coinpayments.net/index.php?cmd=_pay&reset=1&merchant=" \
                   f"{MERCHANT_ID}&item_name=iphone15&currency=USD&amountf=25.00000000&quantity=1&" \
                   "allow_quantity=0&want_shipping=0&allow_extra=1&"

    bot.send_message(user_id, f'برای پرداخت 25 دلار، روی دکمه زیر کلیک کنید:\n[اینجا کلیک کنید]({payment_link})',
                     parse_mode='Markdown')

    # Call the function with the valid txn_id
    result = check_payment_status(txn_id)

    # Notify the user based on the result
    bot.send_message(user_id, result)

def generate_and_print_uuid():
    unique_id = uuid.uuid4()
    return unique_id.hex

def check_payment_status(txn_id):
    # The implementation of this function remains the same as in your original code
    pass

if __name__ == "__main__":
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    bot.polling()
