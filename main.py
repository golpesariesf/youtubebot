import os
import telebot
from flask import Flask, request
from coinpayments import CoinPaymentsAPI

#fff

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
    txn_id = request.text.strip()  # Use request.text instead of message.text
    user_id = message.from_user.id

    if not txn_id or len(txn_id) != 32:
        bot.send_message(user_id, "Invalid transaction ID.")
        return

    # Check payment status
    result = check_payment_status(txn_id)

    # Notify the user based on the result
    bot.send_message(user_id, result)

def check_payment_status(txn_id):
    response = api.get_tx_info(txn_id)
    
    if response['status'] == 100:
        return 'Payment successful!'
    elif response['status'] < 0:
        return 'Payment failed.'
    else:
        return 'Payment is still processing.'

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

@server.route('/ipn', methods=['POST'])
def handle_ipn():
    ipn = request.get_json()
    if not ipn:
        return 'Invalid IPN', 400

    if not api.verify_ipn(ipn, IPN_SECRET):
        return 'Invalid IPN', 400

    # در اینجا شما می‌توانید وضعیت پرداخت را بررسی کنید و به کاربر اطلاع دهید
    # برای مثال، شما می‌توانید از api.get_tx_info استفاده کنید تا اطلاعات تراکنش را بدست آورید
    tx_info = api.get_tx_info(ipn['txn_id'])
    if tx_info['status'] == 100:
        print('پرداخت کامل شده است')
    elif tx_info['status'] < 0:
        print('پرداخت ناموفق بود')
    else:
        print('پرداخت در حال پردازش است')

    return 'OK'
if __name__ == '__main__':
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
