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
IPN_SECRET = '1122334455667788aA@' # Replace with your CoinPayments IPN Secret

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

  # Set fixed amount of 25 USD
  amount = 25

  payload = {
    'version': 1,
    'key': COINPAYMENTS_PUBLIC_KEY,
    'cmd': 'create_payment_button', # Use create_payment_button for a custom button
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
        tx_status = tx_info.get('result', {}).get('status')
        return tx_status
    else:
        print(f"Error getting tx info: {response.status_code}, {response.text}")
        return None

except Exception as e:
    logging.error(f"An error occurred: {str(e)}")
    return None


def handle_callback_query(call):
    user_id = call.from_user.id
    data = call.data

    if data == 'check_payment':
        txn_id = user_states[user_id]
        tx_status = get_tx_info(txn_id)

        if tx_status == 100:
            bot.send_message(user_id, 'پرداخت شما با موفقیت انجام شد! آفرین!')
        elif tx_status in [0, 1, 2]:
            bot.send_message(user_id, 'پرداخت شما در حال انجام است. لطفا منتظر بمانید.')
        else:
            bot.send_message(user_id, 'پرداخت شما با مشکل مواجه شد. لطفا دوباره امتحان کنید.')

    else:
        bot.send_message(user_id, 'اطلاعات نامعتبر')


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_states[user_id] = None

    bot.send_message(user_id, 'به ربات پرداخت خوش آمدید!')
    bot.send_message(user_id, 'برای پرداخت 25 دلار، روی دکمه زیر کلیک کنید:')
    bot.send_message(user_id, 'https://www.coinpayments.net/index.php?cmd=create_payment_button&amount=25&currency1=USD&currency2=BTC&buyer_email=buyer@example.com&success_url=https://youtubenew-c7c31f2cda46.herokuapp.com/7137673728:AAE85wL1RBYskkrlCZaIzhEbgKmiEBiefDI')


@bot.message_handler(func=lambda message: True)
def echo(message):
    user_id = message.from_user.id

    if user_states[user_id] is None:
        # User has not yet initiated payment
        bot.send_message(user_id, 'برای پرداخت 25 دلار، روی دکمه زیر کلیک کنید:')
        bot.send_message(user_id, 'https://www.coinpayments.net/index.php?cmd=create_payment_button&amount=25&currency1=USD&currency2=BTC&buyer_email=buyer@example.com&success_url=https://youtubenew-c7c31f2cda46.herokuapp.com/7137673728:AAE85wL1RBYskkrlCZaIzhEbgKmiEBiefDI')


if __name__ == '__main__':
    bot.polling()

