import uuid
import json
import requests
import os
import time
import logging
from datetime import timedelta
from typing import Any
from googleapiclient.discovery import build
from google.oauth2 import service_account

BASE_PATH = '/mnt/data'

EXCHANGE_FOLDER = BASE_PATH + '/exchange_files'

EXCHANGE_OLD_FOLDER = BASE_PATH + '/exchange_files_old'

CONFIG: dict = {
    'enrivonment': 'production',
    'development': {
        'db_file_location': '/Users/mcarlos/Documents/BitBucket/base/dbs.json'
    },
    'production': {
        'db_file_location': '/mnt/data/dbs.json'
    }
}

def get_config():
    return CONFIG[CONFIG['enrivonment']]

OPERATIONS_DATA_TYPES = {
    'current_orders': [],
    'current_orders_count': ['snap', 'incr', 'avg'],
    'current_orders_amounts': ['snap', 'incr', 'avg'],
    'current_orders_mid_prices': ['incr'],
    'current_values': ['snap'],
    'current_pnls': ['snap'],
    'tickers': ['snap'],
    'trades': ['snap', 'incr'],
    'order_books': ['snap']
}

PERIODS = {
    '1m': 1,
    '5m': 5,
    '30m': 30,
    '1h': 60,
    '4h': 240,
    '12h': 720,
    '24h': 1440
}

DIFF_BUY_SELL_LIMIT_TO_INACTIVATE_VOL_BOT: dict = {
    'DAMEX': 700
}

MIN_BALANCE_TO_INACTIVATE_VOL_BOT: dict = {
    'DAMEX': 1000,
    'USDT': 10,
    'USDC': 10
}

SOLANA_TOKENS: dict = {
    'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB': 'USDT',
    'H3cb6GkPPnT7USCebarN8KtHRTa6Ea3ynF3XfUMeVnVh': 'DAMEX',
    'So11111111111111111111111111111111111111112': 'SOL',
    'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v': 'USDC',
    '6zoshtkmyX4kRFg3p152yV2bPssxeYdNvW3c6EVCE4UP': 'PRICK'
}

def send_alert(alert_type: str, message_values: dict, channel: str):
    alerts_folder = '/mnt/data/alert_files'
    f = open(alerts_folder + '/' + str(uuid.uuid4()) + '.json', 'w+', encoding='UTF-8')
    f.write(json.dumps({
        'type': alert_type,
        'message_values': message_values,
        'channel': channel
    }))
    f.close()   
    
def write_to_google_spreadsheet(spreadsheet_id: str, values: list[list], sheet_id: str):
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    KEY = '/mnt/data/google_key.json'
    creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().append(spreadsheetId=spreadsheet_id,
							range=sheet_id + '!A1',
							valueInputOption='USER_ENTERED',
							body={'values':values}).execute()
    logging.getLogger(__name__).info("Updated %s cells", result.get('updates').get('updatedCells'))

async def http_request_damex(method: str, url: str, headers: dict = None, retry: int = 0, data: dict = None):
    response = None
    i = 0
    while i < retry + 1:
        if method == 'GET':
            response = requests.get(url=url, headers=headers, timeout=7)
        elif method == 'POST':
            response = requests.post(url=url, headers=headers, json=data, timeout=7)
        else:
            logging.getLogger(__name__).info('method %s not supported', method)
            raise Exception
        if response.status_code == 200:
            break
        if response.status_code == 500:
            i += 1
            logging.getLogger(__name__).error('%s %s %s', url, data, response)
            logging.getLogger(__name__).info('retrying %s %s', url, data)
            time.sleep(2)
            continue
        else:
            logging.getLogger(__name__).error('%s %s %s', url, data, response)
            raise Exception
    if response.status_code != 200:
        logging.getLogger(__name__).error('%s %s %s', url, data, response)
        raise Exception
    response_data = response.json()
    logging.getLogger(__name__).info('%s %s %s', url, data, response_data)
    return response_data

def get_period_name(period_in_minutes):
    match period_in_minutes:
        case 1:
            return '1m'
        case 5:
            return '5m'
        case 30:
            return '30m'
        case 60:
            return '1h'
        case 240:
            return '4h'
        case 720:
            return '12h'
        case 1440:
            return '24h'

def get_period_datetime(datetime, period):
    if period == '1m' or period == 1:
        period_datetime = datetime.replace(second=0, microsecond=0) + timedelta(minutes=1)
    elif period == '5m' or period == 5:
        minutes = datetime.minute // 5 * 5
        period_datetime = datetime.replace(second=0, microsecond=0, minute=minutes) + timedelta(minutes=5)
    elif period == '15m' or period == 15:
        minutes = datetime.minute // 15 * 15
        period_datetime = datetime.replace(second=0, microsecond=0, minute=minutes) + timedelta(minutes=15)
    elif period == '30m' or period == 30:
        minutes = datetime.minute // 30 * 30
        period_datetime = datetime.replace(second=0, microsecond=0, minute=minutes) + timedelta(minutes=30)
    elif period == '1h' or period == 60:
        period_datetime = datetime.replace(second=0, microsecond=0, minute=0) + timedelta(hours=1)
    elif period == '4h' or period == 240:
        hours = datetime.hour // 4 * 4
        period_datetime = datetime.replace(second=0, microsecond=0, minute=0, hour=hours) + timedelta(hours=4)
    elif period == '12h' or period == 720:
        hours = datetime.hour // 12 * 12
        period_datetime = datetime.replace(second=0, microsecond=0, minute=0, hour=hours) + timedelta(hours=12)
    elif period == '1D' or period == '24h' or period == 1440:
        period_datetime = datetime.replace(second=0, microsecond=0, minute=0, hour=0) + timedelta(days=1)
        
    return period_datetime

def add_data_exchange_file(file_name, data, exchange, operation, market):
    exchange_folder = EXCHANGE_FOLDER + '/' + exchange
    if not os.path.exists(exchange_folder):
        os.makedirs(exchange_folder)
    operation_exchange_folder = exchange_folder + '/' + operation
    if not os.path.exists(operation_exchange_folder):
        os.makedirs(operation_exchange_folder)
    market_operation_exchange_folder = operation_exchange_folder + '/' + market
    if not os.path.exists(market_operation_exchange_folder):
        os.makedirs(market_operation_exchange_folder)
    if os.path.exists(market_operation_exchange_folder + '/' + file_name):
        return
    f = open(market_operation_exchange_folder + '/' + file_name, 'w+', encoding='UTF-8')
    f.write(json.dumps(data))
    f.close()
    if os.path.exists(market_operation_exchange_folder + '/info.json'):
        with open(market_operation_exchange_folder + '/info.json', "r", encoding='UTF-8') as jsonFile:
            info = json.load(jsonFile)
    else:
        info = {}
    info['last_file_name'] = file_name
    with open(market_operation_exchange_folder + '/info.json', "w", encoding='UTF-8') as jsonFile:
        json.dump(info, jsonFile)
        
def add_to_info(key: str, value: Any, action: str, exchange: str, operation: str, market: str):
    market_operation_exchange_folder = EXCHANGE_FOLDER + '/' + exchange + '/' + operation + '/' + market
    if os.path.exists(market_operation_exchange_folder + '/info.json'):
        info = json.loads(open(market_operation_exchange_folder + '/info.json', 'r', encoding='UTF-8').read())
        if action == 'replace':
            info[key] = value
        elif action == 'add':
            if not key in info:
                info[key] = []
            info[key].append(value)
            if len(info[key]) > 101:
                info[key].pop(0)                
        f = open(market_operation_exchange_folder + '/info.json', 'w+', encoding='UTF-8')
        f.write(json.dumps(info))
        f.close()
        
def add_last_price_and_last_ticker_to_info(last_price: float, volume: float, exchange: str, operation: str, market: str):
    market_operation_exchange_folder = EXCHANGE_FOLDER + '/' + exchange + '/' + operation + '/' + market
    if os.path.exists(market_operation_exchange_folder + '/info.json'):
        info = json.loads(open(market_operation_exchange_folder + '/info.json', 'r', encoding='UTF-8').read())
        if 'last_trade_price' in info and float(info['last_trade_price']) != float(last_price):
            info['last_trade_price'] = last_price
        elif not 'last_trade_price' in info:
            info['last_trade_price'] = last_price
        last_ticker = {'timestamp': int(time.time() * 1000), 'last_price': last_price, 'volume': volume}
        if 'last_tickers' in info:
            info['last_tickers'].append(last_ticker)
            if len(info['last_tickers']) > 101:
                info['last_tickers'].pop(0)
        elif not 'last_tickers' in info:
            info['last_tickers'] = [last_ticker]
        with open(market_operation_exchange_folder + '/info.json', "w", encoding='UTF-8') as jsonFile:
            json.dump(info, jsonFile)
