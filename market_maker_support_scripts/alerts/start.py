import json
import time
import logging
from datetime import datetime
import pytz
import os
from logging.handlers import RotatingFileHandler
import requests
import asyncio
from threading import Thread
from psycopg2 import Error
from damexCommons.tools.damex_http_client import get_main_price
from damexCommons.tools.dbs import get_exchange_db
from damexCommons.tools.utils import BASE_PATH

exchange_db = get_exchange_db(db_connection='support_scripts')
operation = 'alerts'

logging.basicConfig(
    level=logging.INFO, 
    handlers=[
        RotatingFileHandler(f"{operation}.log", mode='a', maxBytes=1024*1024*10, backupCount=10, encoding=None, delay=0),
        logging.StreamHandler()
    ],
    format="%(asctime)s %(levelname)s %(message)s"
)

def send_message_on_telegram(message, telegram_group_id, telegram_auth_token):
    telegram_api_url = f"https://api.telegram.org/bot{telegram_auth_token}/sendMessage?chat_id=@{telegram_group_id}&text={message}"
    telelegram_resp = requests.get(telegram_api_url, timeout=7)
    if telelegram_resp.status_code == 200:
        logging.info("Notification has been sent on Telegram") 
    else:
        logging.info("Could not send Message")
        
def parse_message(message: str, message_values: dict):
    current_datetime = datetime.now(pytz.timezone('UTC'))
    message_values['date'] = current_datetime.strftime("%d-%m-%Y")
    message_values['time'] = current_datetime.strftime("%H:%M:%S")
    for message_value in message_values:
        key = '$' + str(message_value).upper()
        message = message.replace(key, str(message_values[message_value]))
    
    return message

def run_price_change_percent_alert(alert: dict, main_price: float):
    current_time = int(time.time() * 1000)
    telegram_group_id = alert['telegram_group_id']
    telegram_auth_token = alert['telegram_auth_token']
    logging.info('-------------------------------------------------------------------')
    logging.info('run_price_change_percent_alert')
    for market in alert['config']:
        initial_time = current_time - (int(alert['config'][market]['period']) * 60 * 1e3)        
        for exchange in alert['exchanges']:
            logging.info('---------------------------------------')
            logging.info('exchange %s', exchange)
            logging.info('market %s', market)
            exchange_operation_market_folder = BASE_PATH + '/exchange_files' + '/' + exchange + '/ticker/' + market
            info_file = exchange_operation_market_folder + '/info.json'
            info = json.loads(open(info_file, 'r', encoding='UTF-8').read())
            last_trade_price = round(float(info['last_trade_price']), 5)
            last_tickers = info['last_tickers']
            initial_price = None
            for ticker in last_tickers:
                if int(ticker['timestamp']) > initial_time:
                    initial_price = float(ticker['last_price'])
                    break
            if initial_price is None:
                initial_price = float(last_tickers[len(last_tickers) - 1]['last_price'])
                    
            price_change_percent = round((last_trade_price - initial_price) * 100 / initial_price, 2)
            if price_change_percent > int(alert['config'][market]['up']) or price_change_percent < -1 * int(alert['config'][market]['down']):
                message = parse_message(alert['message_output'], {
                    'exchange': exchange,
                    'market': market,
                    'trade_price_change_percent': price_change_percent,
                    'period': alert['config'][market]['period'],
                    'trade_price': last_trade_price,
                    'main_price': main_price
                })
                logging.info('message %s', message)
                send_message_on_telegram(message=message, telegram_group_id=telegram_group_id, telegram_auth_token=telegram_auth_token)
            logging.info('---------------------------------------')
    logging.info('-------------------------------------------------------------------')
        
def run_balance_out_of_limits_alert(alert: dict):
    telegram_group_id = alert['telegram_group_id']
    telegram_auth_token = alert['telegram_auth_token']
    logging.info('-------------------------------------------------------------------')
    logging.info('run_balance_out_of_limits_alert')
    for exchange in alert['exchanges']:
        logging.info('---------------------------------------')
        logging.info('exchange %s', exchange)
        balance_folder = BASE_PATH + '/exchange_files' + '/' + exchange + '/current_values/NONE'
        balance_folder_old = BASE_PATH + '/exchange_files_old' + '/' + exchange + '/current_values/NONE'
        info = json.loads(open(balance_folder + '/info.json', 'r', encoding='UTF-8').read())
        last_balance_file = balance_folder + '/' + info['last_file_name']
        if not os.path.isfile(last_balance_file):
            last_balance_file = balance_folder_old + '/' + info['last_file_name']
        last_balance = json.loads(open(last_balance_file, 'r', encoding='UTF-8').read())
        for data in last_balance['values']:  
            for asset in alert['config']:
                if data['currency'] == asset:
                    balance = float(data['amount'])
                    if balance <= float(alert['config'][asset]['min']) or balance >= float(alert['config'][asset]['max']):
                        message = parse_message(alert['message_output'], {
                            'exchange': exchange,
                            'asset': asset,
                            'balance': round(float(balance), 2)
                        })
                        logging.info('message %s', message)
                        send_message_on_telegram(message=message, telegram_group_id=telegram_group_id, telegram_auth_token=telegram_auth_token)
                    break
        logging.info('---------------------------------------')
    logging.info('-------------------------------------------------------------------')

def run_maker_orders_out_of_range_alert(alert: dict):
    telegram_group_id = alert['telegram_group_id']
    telegram_auth_token = alert['telegram_auth_token']
    logging.info('-------------------------------------------------------------------')
    logging.info('run_maker_orders_out_of_range_alert')
    for exchange in alert['exchanges']:
        for market in alert['config']:
            base_asset = market.split('-')[0]
            quote_asset = market.split('-')[1]
            orders_count_by_side = asyncio.run(exchange_db.fetch_open_orders_count_db(exchange=exchange, base_asset=base_asset, quote_asset=quote_asset, sides=[1, 2]))
            logging.info('---------------------------------------')
            logging.info('exchange %s', exchange)
            logging.info('market %s', market)
            logging.info('orders_count_by_side %s', orders_count_by_side)
            if orders_count_by_side['ASK'] <= int(alert['config'][market]['ask_min']) or orders_count_by_side['BID'] <= int(alert['config'][market]['bid_min']) or orders_count_by_side['ASK'] >= int(alert['config'][market]['ask_max']) or orders_count_by_side['BID'] >= int(alert['config'][market]['bid_max']):
                message = parse_message(alert['message_output'], {
                    'exchange': exchange,
                    'market': market,
                    'bid_orders_count': orders_count_by_side['BID'],
                    'ask_orders_count': orders_count_by_side['ASK'],
                })
                logging.info('message %s', message)
                send_message_on_telegram(message=message, telegram_group_id=telegram_group_id, telegram_auth_token=telegram_auth_token)
            logging.info('---------------------------------------')
    logging.info('-------------------------------------------------------------------')            
        
def run_ask_ceiling_or_bid_floor_discover_alert(alert: dict, main_price: float):
    telegram_group_id = alert['telegram_group_id']
    telegram_auth_token = alert['telegram_auth_token']
    logging.info('-------------------------------------------------------------------')
    logging.info('run_ask_ceiling_or_bid_floor_discover_alert')
    for market in alert['config']:
        for exchange in alert['exchanges']:
            logging.info('---------------------------------------')
            logging.info('exchange %s', exchange)
            logging.info('market %s', market)
            base_asset = market.split('-')[0]
            quote_asset = market.split('-')[1]
            order_books_folder = BASE_PATH + '/exchange_files' + '/' + exchange + '/order_books/' + market
            info_file = order_books_folder + '/info.json'
            public_order_book_file = json.loads(open(info_file, 'r', encoding='UTF-8').read())['last_file_name']
            public_order_book = json.loads(open(order_books_folder + '/' + public_order_book_file, 'r', encoding='UTF-8').read())
            private_order_book = asyncio.run(exchange_db.get_order_book_db(base_asset=base_asset, quote_asset=quote_asset, size=100, exchange=exchange))            
            
            logging.info('private_order_book %s', private_order_book)
            logging.info('public_order_book_bids %s', public_order_book)
            
            #public_order_book['bids'].insert(0, [0.0311, 1000])
            #public_order_book['bids'].insert(0, [0.0312, 1000])
            #public_order_book['bids'].insert(0, [0.0313, 1000])
            #public_order_book['bids'].insert(0, [0.0314, 1000])
                        
            if len(private_order_book['asks']) > 0:
                private_ask_price = float(private_order_book['asks'][0][0])
                levels_banding_price_quantity = 0
                levels_banding_price_total = 0
                for level in public_order_book['asks']:
                    level_price = float(level[0])
                    level_amount = float(level[1])
                    if level_price < private_ask_price and level_price < main_price:
                        levels_banding_price_quantity +=1
                        levels_banding_price_total += level_price * level_amount
                    else:
                        break
                if levels_banding_price_quantity > 0:
                    message = parse_message(alert['message_output'], {
                        'exchange': exchange,
                        'market': market,
                        'floor_or_ceiling': 'ceiling',
                        'orders_number': levels_banding_price_quantity,
                        'amount': round(float(levels_banding_price_total), 5),
                        'quote_asset': quote_asset
                    })
                    logging.info('message %s', message)
                    send_message_on_telegram(message=message, telegram_group_id=telegram_group_id, telegram_auth_token=telegram_auth_token)
    
            if len(private_order_book['bids']) > 0:
                private_bid_price = float(private_order_book['bids'][0][0])
                levels_banding_price_quantity = 0
                levels_banding_price_total = 0
                for level in public_order_book['bids']:
                    level_price = float(level[0])
                    level_amount = float(level[1])
                    if level_price > private_bid_price and level_price > main_price:
                        levels_banding_price_quantity +=1
                        levels_banding_price_total += level_price * level_amount
                    else:
                        break
                if levels_banding_price_quantity > 0:
                    message = parse_message(alert['message_output'], {
                        'exchange': exchange,
                        'market': market,
                        'floor_or_ceiling': 'floor',
                        'orders_number': levels_banding_price_quantity,
                        'amount': round(float(levels_banding_price_total), 5),
                        'quote_asset': quote_asset
                    })
                    logging.info('message %s', message)
                    send_message_on_telegram(message=message, telegram_group_id=telegram_group_id, telegram_auth_token=telegram_auth_token)
    
            logging.info('---------------------------------------')
    logging.info('-------------------------------------------------------------------')
        
        
while True:
    try:
        alerts = asyncio.run(exchange_db.fetch_active_alerts_db())
        logging.info('alerts %s %s', alerts, len(alerts))
        
        for alert in alerts:
            main_price = asyncio.run(get_main_price(base_asset='DAMEX', quote_asset='USDT', price_decimals=5))
            match alert['type']:
                case 'price_change_percent':
                    t_price_change_percent = Thread(target=run_price_change_percent_alert, args=[alert, main_price])
                    t_price_change_percent.run()
                case 'balance_out_of_limits':
                    t_balance_out_of_limits = Thread(target=run_balance_out_of_limits_alert, args=[alert])
                    t_balance_out_of_limits.run()
                case 'maker_orders_out_of_range':
                    t_maker_orders_out_of_range = Thread(target=run_maker_orders_out_of_range_alert, args=[alert])
                    t_maker_orders_out_of_range.run()
                case 'ask_ceiling_or_bid_floor_discover': 
                    t_ask_ceiling_or_bid_floor_discover = Thread(target=run_ask_ceiling_or_bid_floor_discover_alert, args=[alert, main_price])
                    t_ask_ceiling_or_bid_floor_discover.run()
        time.sleep(60)
                    
    except (Exception, Error) as error:
        logging.error("Error trying to process the script %s", error)
        time.sleep(5)
