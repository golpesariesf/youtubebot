# Import required modules
import sys
from flask import Flask, request, jsonify
import json
import hmac
import hashlib
import logging
import requests
import uuid
from coinpayments import CoinPaymentsAPI
import os

# Set up logging
logging.basicConfig(filename='bot_log.txt', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Telegram bot configuration
TOKEN = '7095077129:AAE-rDWtk6q7S8ZgkxmcfLtnJdMtAYJutq4'
APP_URL = f'https://youtubenew-c7c31f2cda46.herokuapp.com/{TOKEN}'

# CoinPayments configuration
COINPAYMENTS_PUBLIC_KEY = '616e319dad674f8906f129a735d299d6665388a0fe3f4e075ffc3e2b9c3ce8f3'
COINPAYMENTS_PRIVATE_KEY = 'D544Edec2fa5725C5913C5806665393ec58769563f5C7477DfBb8A8C4302867b'
IPN_SECRET = '1122334455667788aA@'  # Replace with your CoinPayments IPN Secret
MERCHANT_ID = "c80ec2928c4b6836e6ada19db1c229ec"

# Initialize Flask app
app = Flask(__name__)

# Initialize CoinPayments API
api = CoinPaymentsAPI(public_key=COINPAYMENTS_PUBLIC_KEY, private_key=COINPAYMENTS_PRIVATE_KEY)

# Routes for Flask app
@app.route('/')
def index():
    return 'Hello, this is your Flask app!'

@app.route('/')
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    return 'Webhook set successfully!', 200


@app.route('/payment/<txn_id>', methods=['GET'])
def handle_payment(txn_id):
    user_id = request.args.get('user_id')

    if not txn_id or len(txn_id) != 32:
        return jsonify({"error": "Invalid transaction ID"}), 400

    payment_link = f"https://www.coinpayments.net/index.php?cmd=_pay&reset=1&merchant={MERCHANT_ID}&item_name=iphone15&currency=USD&amountf=25.00000000&quantity=1&allow_quantity=0&want_shipping=0&allow_extra=1"

    return jsonify({"message": f"Click [here]({payment_link}) to pay $25.", "user_id": user_id}), 200

@app.route('/ipn', methods=['POST'])
def handle_ipn():
    ipn = request.get_json()

    if not ipn or not verify_ipn_signature(ipn):
        return jsonify({"error": "Invalid IPN"}), 400

    tx_info = api.get_tx_info(ipn['txn_id'])
    if tx_info['status'] == 100:
        print('Payment has been completed successfully')
    elif tx_info['status'] < 0:
        print('Payment was unsuccessful')
    else:
        print('Payment is in progress')

    return jsonify({"message": "OK"}), 200

def verify_ipn_signature(data):
    expected_signature = hmac.new(
        IPN_SECRET.encode(),
        json.dumps(data, sort_keys=True).encode(),
        hashlib.sha512
    ).hexdigest()

    return data.get("hmac") == expected_signature

# Run the Flask app
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
