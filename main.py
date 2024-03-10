﻿import telebot
from flask import Flask
import os
import requests
import json
import hashlib
from telebot import types

TOKEN = '7095077129:AAE-rDWtk6q7S8ZgkxmcfLtnJdMtAYJutq4'
APP_URL = f'https://youtubenew-c7c31f2cda46.herokuapp.com/{TOKEN}'

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)
COINPAYMENTS_PUBLIC_KEY = '616e319dad674f8906f129a735d299d6665388a0fe3f4e075ffc3e2b9c3ce8f3'
COINPAYMENTS_PRIVATE_KEY = 'D544Edec2fa5725C5913C5806665393ec58769563f5C7477DfBb8A8C4302867b'
IPN_SECRET = '1122334455667788aA@'

class CoinPaymentsAPI:
def __init__(self, public_key, private_key):
self.public_key = public_key
self.private_key = private_key

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

post_data = '&'.join([f'{key}={req[key]}' for key in req])
hmac_hash = hashlib.sha512(post_data.encode('utf-8'), self.private_key.encode('utf-8')).hexdigest()

headers = {'HMAC': hmac_hash}
response = requests.post('https://www.coinpayments.net/api.php', data=req, headers=headers)

try:
data = response.json()
return data
except json.JSONDecodeError:
return {'error': 'Unable to parse JSON result.'}

api = CoinPaymentsAPI(public_key=COINPAYMENTS_PUBLIC_KEY, private_key=COINPAYMENTS_PRIVATE_KEY)

@bot.message_handler(commands=['start'])
def start(message):
user_id = message.from_user.id
markup = types.InlineKeyboardMarkup()
link_button = types.InlineKeyboardButton("Click here to pay", url='https://www.coinpayments.net/index.php?cmd=_pay&reset=1&merchant=c80ec2928c4b6836e6ada19db1c229ec&item_name=iphone15&currency=USD&amountf=25.00000000&quantity=1&allow_quantity=0&want_shipping=0&allow_extra=1&%27)')
markup.add(link_button)

bot.reply_to(message, "To make a payment, click on the button below:", reply_markup=markup)

@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo(message):
txn_id = message.text.strip()
user_id = message.from_user.id

if not txn_id or len(txn_id) != 32:
bot.send_message(user_id, "Invalid transaction ID.")
return

result = api.check_payment_status(txn_id)
bot.send_message(user_id, result)

if __name__ == '__main__':
server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))