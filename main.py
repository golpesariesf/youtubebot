# Add the path to the virtual environment's site-packages directory
import sys
sys.path.append('/home/Biamoozim/venv/lib/python3.10/site-packages')

# Rest of your code goes here...


import telebot
from flask import Flask, request
import json
import hmac
import hashlib
import logging
import requests
import uuid
from coinpayments_py import CoinPaymentsAPI



# Setup logging
logging.basicConfig(filename='bot_log.txt', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
TOKEN = '7137673728:AAE85wL1RBYskkrlCZaIzhEbgKmiEBiefDI'
APP_URL = f'https://biamoozim.pythonanywhere.com/{TOKEN}'
COINPAYMENTS_PUBLIC_KEY = '616e319dad674f8906f129a735d299d6665388a0fe3f4e075ffc3e2b9c3ce8f3'
COINPAYMENTS_PRIVATE_KEY = 'D544Edec2fa5725C5913C5806665393ec58769563f5C7477DfBb8A8C4302867b'
IPN_SECRET = '1122334455667788aA@' # Replace with your CoinPayments IPN Secret
MERCHANT_ID = "c80ec2928c4b6836e6ada19db1c229ec" # اضافه کنید


bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)
bot.remove_webhook()
user_states = {}


def generate_and_print_uuid():
    unique_id = uuid.uuid4()
    return unique_id.hex


def check_payment_status(txn_id):
    response = requests.get(
        "https://www.coinpayments.net/api.php",
        params={
            "cmd": "get_tx_info",
            "txid": txn_id,
            "key": COINPAYMENTS_PUBLIC_KEY,
        }
    )

    if response.status_code in [200, 400, 401]:
        data = response.json()

        if isinstance(data, list):
            data = data[0]

        status = data.get("result", {}).get("status")
        status_text = data.get("result", {}).get("status_text")

        if status == 100:
            return "پرداخت شما با موفقیت انجام شد!"
        elif status in [0, 1, 2]:
            return f"پرداخت شما در حال انجام است. لطفا منتظر بمانید.\n\nوضعیت فعلی: {status_text}"
        else:
            return f"پرداخت شما با مشکل مواجه شده است. لطفا دوباره امتحان کنید.\n\nوضعیت فعلی: {status_text}"
    else:
        logging.error(f"API request failed with status code: {response.status_code}")

        if response.status_code == 401:
            logging.error("Invalid API key.")
            return "خطا در احراز هویت API. لطفا کلید عمومی خود را بررسی کنید."

        if response.status_code == 400:
            logging.error(f"API request failed with error: {response.text}")
            return "خطا در درخواست API. لطفا پارامترهای ارسالی را بررسی کنید."


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


api = CoinPaymentsAPI(public_key=COINPAYMENTS_PUBLIC_KEY, private_key=COINPAYMENTS_PRIVATE_KEY)


@app.route('/ipn', methods=['POST'])
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


def verify_ipn_signature(data):
    expected_signature = hmac.new(
        IPN_SECRET.encode(),
        json.dumps(data, sort_keys=True).encode(),
        hashlib.sha512
    ).hexdigest()

    return data.get("hmac") == expected_signature


if __name__ == "__main__":
    bot.polling()
