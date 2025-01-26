import json
import asyncio
import os
from channels.generic.websocket import WebsocketConsumer
from ..notifiers_wss.exchange_api import NotifierExchangeAPI
from ..watchers_wss.exchange_api import WatcherExchangeAPI
from ..utils import DATA_FOLDER, DATA_OLD_FOLDER
from damexCommons.tools.dbs import get_exchange_db
from damexCommons.tools.exchange import get_order_book_price


notifier_exchange_api = None
watcher_exchange_api = None

exchange_db = get_exchange_db(db_connection='exchange_connector')

class ExchangeAPIConsumer(WebsocketConsumer):
    
    def connect(self):
        self.accept()
        self.send(text_data=json.dumps({
            'type': 'connection-established',
            'message': 'You are now connected!'
        }))

    def disconnect(self, code):
        print('disconnect')
        if notifier_exchange_api is not None:
            notifier_exchange_api.unsubscribe_websocket_client(self, None)
        if watcher_exchange_api is not None:
            watcher_exchange_api.unsubscribe_websocket_client(self, None)

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        id = text_data_json['id']
        operation = text_data_json['operation']
        method = text_data_json['method']
        params = text_data_json['params']
        response = {
            "id": id,
            "operation": operation,
            "params": params,
            "type": "old",
            "data": []
        }
        global notifier_exchange_api
        if notifier_exchange_api is None:
            notifier_exchange_api = NotifierExchangeAPI()
            notifier_exchange_api.run()
            print('NOTIFIER EXCHANGE API INITIATED')
        
        global watcher_exchange_api
        if watcher_exchange_api is None:
            watcher_exchange_api = WatcherExchangeAPI()
            watcher_exchange_api.run()
            print('WATCHER EXCHANGE API INITIATED')
        
        allowed_operations = ['order_book', 'order_book_price', 'trades', 'market_info', 'main_price']
        
        if operation not in allowed_operations:
            self.send(text_data=json.dumps(
                {"type": "error", "message": "operation is not allowed!"}))
            return
        
        if method != 'subscribe' and method != 'snapshot' and method != 'unsubscribe':
            self.send(text_data=json.dumps(
                {"type": "error", "message": "method is not allowed!"}))
            return
        
        if method == 'subscribe' or method == 'snapshot':
            if operation == 'order_book':
                if not 'market' in params:
                    self.send(text_data=json.dumps({"type": "error", "message": "market param is needed!"}))
                    return
                market = params['market']
                size = 10
                if 'size' in params:
                    size = int(params['size'])
                else:
                    size = params['size']
                response['data'] = add_order_book_old_data(market=market, size=size)
        
            if operation == 'order_book_price':
                if not 'market' in params:
                    self.send(text_data=json.dumps({"type": "error", "message": "market param is needed!"}))
                    return
                if not 'amount' in params:
                    self.send(text_data=json.dumps({"type": "error", "message": "amount param is needed!"}))
                    return
                if not 'currency' in params:
                    self.send(text_data=json.dumps({"type": "error", "message": "currency param is needed!"}))
                    return
                if not 'side' in params:
                    self.send(text_data=json.dumps({"type": "error", "message": "side param is needed!"}))
                    return
                if params['side'] != 'buy' and params['side'] != 'sell':
                    self.send(text_data=json.dumps({"type": "error", "message": "side param must be buy or sell!"}))
                    return
                market = params['market']
                amount = float(params['amount'])
                currency = params['currency']
                side = params['side']
                response['data'] = add_order_book_price_old_data(market=market, amount=amount, currency=currency, side=side)

            if operation == 'trades':
                if not 'market' in params:
                    self.send(text_data=json.dumps({"type": "error", "message": "market param is needed!"}))
                    return
                market = params['market']
                response['data'] = add_trades_old_data(market=market)
                
            if operation == 'market_info':
                if not 'market' in params:
                    self.send(text_data=json.dumps({"type": "error", "message": "market param is needed!"}))
                    return
                market = params['market']
                response['data'] = []
                
            if operation == 'main_price':
                if not 'market' in params:
                    self.send(text_data=json.dumps({"type": "error", "message": "market param is needed!"}))
                    return
                if not 'period' in params:
                    self.send(text_data=json.dumps({"type": "error", "message": "period param is needed!"}))
                    return
                if not 'size' in params:
                    self.send(text_data=json.dumps({"type": "error", "message": "size param is needed!"}))
                    return
                market = params['market']
                period = params['period']
                size = int(params['size'])
                response['data'] = add_main_price_old_data(market=market, period=period, size=size)

            self.send(text_data=json.dumps(response))
        
        if method == 'snapshot' or response['data'] is None:
            return
        
        self.id = id
        thread = {
            'operation': operation,
            'params': params
        }
        
        if (operation == 'order_book' or operation == 'order_book_price'):
            if method == 'subscribe':
                notifier_exchange_api.subscribe_websocket_client(self, thread)
            elif method == 'unsubscribe':
                notifier_exchange_api.unsubscribe_websocket_client(self, thread)
        elif (operation == 'trades' or operation == 'main_price' or operation == 'ticker' or operation == 'market_info'):
            if method == 'subscribe':
                watcher_exchange_api.subscribe_websocket_client(self, thread)
            elif method == 'unsubscribe':
                watcher_exchange_api.unsubscribe_websocket_client(self, thread)
        
def add_order_book_old_data(market: str, size: int):
    return asyncio.run(exchange_db.get_order_book_db(base_asset=market.split('-')[0], quote_asset=market.split('-')[1], size=size))

def add_order_book_price_old_data(market: str, amount: float, currency: str, side: str):
    return asyncio.run(get_order_book_price(base_asset=market.split('-')[0], quote_asset=market.split('-')[1], currency=currency, side=side, amount=amount))

def add_trades_old_data(market: str):
    if market == 'DAMEX-USDT':
        exchanges = ['APP']
        exchanges.extend(['bitmart', 'coinstore', 'mexc', 'tidex', 'ascendex'])
    elif market == 'HOT-USDT':
        exchanges = ['binance']
    trades_timestamp = {}
    for exchange in exchanges:
        info_file = '%s/%s/%s/%s/%s' % (DATA_FOLDER, exchange, 'trades', market, 'info.json')
        if not os.path.exists(info_file):
            continue
        try:
            info = json.loads(open(info_file, 'r', encoding='UTF-8').read())
        except Exception as e:
            print('exception', e)
            continue
        last_file_name = info['last_file_name']
        trade_file = '%s/%s/%s/%s/%s' % (DATA_FOLDER, exchange, 'trades', market, last_file_name)
        if not os.path.exists(trade_file):
            trade_file = '%s/%s/%s/%s/%s' % (DATA_OLD_FOLDER, exchange, 'trades', market, last_file_name)
        if not os.path.exists(trade_file):
            continue
        trade = json.loads(open(trade_file, 'r', encoding='UTF-8').read())
        timestamp = trade['timestamp']
        trades_timestamp[timestamp] = trade
    
    trades_timestamp = sort(trades_timestamp, reverse=True)
    trades = []    
    for timestamp in trades_timestamp:
        trades.append(trades_timestamp[timestamp])
    
    return trades

def add_main_price_old_data(market: str, period: int, size: int):
    print('market period size', market, period, size)
    return {}
                
def sort(object: dict={}, reverse: bool=False) -> dict: 
    sorted_object = {}
    for i in sorted(object.keys(), key=float, reverse=reverse):
        sorted_object[i] = object[i]
    return sorted_object                
