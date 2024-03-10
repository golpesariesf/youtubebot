from coinpayments import CoinPaymentsAPI
import uuid
import telebot
from flask import Flask, request
import os
import requests
import json
import hashlib

TOKEN = '7095077129:AAE-rDWtk6q7S8ZgkxmcfLtnJdMtAYJutq4'
APP_URL = f'https://youtubenew-c7c31f2cda46.herokuapp.com/{TOKEN}'

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)
COINPAYMENTS_PUBLIC_KEY = '616e319dad674f8906f129a735d299d6665388a0fe3f4e075ffc3e2b9c3ce8f3'
COINPAYMENTS_PRIVATE_KEY = 'D544Edec2fa5725C5913C5806665393ec58769563f5C7477DfBb8A8C4302867b'
IPN_SECRET = '1122334455667788aA@'

api = CoinPaymentsAPI(public_key=COINPAYMENTS_PUBLIC_KEY, private_key=COINPAYMENTS_PRIVATE_KEY)

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
      class CoinPaymentsAPI:
        def __init__(self, public_key, private_key):
            self.public_key = public_key
            self.private_key = private_key
            self.ch = None

        def check_payment_status(self, txn_id):
            response = self.api_call('get_tx_info', {'txid': txn_id})

            if 'status' not in response:
                return 'Invalid response from CoinPayments API.'

            if response['status'] == 100:
                return 'Payment successful!'
            elif response['status'] < 0:
                return 'Payment failed.'
            else:
                return 'Payment is still processing.'

        def api_call(self, cmd, req={}):
            if not self.public_key or not self.private_key:
                return {'error': 'You have not set your public and private keys!'}

            req['version'] = 1
            req['cmd'] = cmd
            req['key'] = self.public_key
            req['format'] = 'json'

            post_data = '&'.join([f'{key}={value}' for key, value in req.items()])
            hmac = hashlib.sha512(post_data.encode('utf-8')).hexdigest()

            if self.ch is None:
                self.ch = requests.Session()

            headers = {'HMAC': hmac}
            response = self.ch.post('https://www.coinpayments.net/api.php', data=req, headers=headers)

            try:
                dec = response.json()
                if dec and isinstance(dec, dict):
                    return dec
                else:
                    return {'error': f'Unable to parse JSON result ({json.dumps(dec)})'}
            except json.JSONDecodeError as e:
                return {'error': f'Unable to parse JSON result ({str(e)})'}

# Example usage:
txn_id_to_check = 'YOUR_TRANSACTION_ID'
public_key = '616e319dad674f8906f129a735d299d6665388a0fe3f4e075ffc3e2b9c3ce8f3'
private_key = 'D544Edec2fa5725C5913C5806665393ec58769563f5C7477DfBb8A8C4302867b'

# CoinPaymentsAPI object should be created before using it
coinpayments_api = CoinPaymentsAPI(public_key, private_key)

# Use the created object to call the check_payment_status method
payment_status = coinpayments_api.check_payment_status(txn_id_to_check)
print(payment_status)

# Notify the user based on the result
bot.send_message(user_id, payment_status)


if __name__ == '__main__':
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
