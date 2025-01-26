import json
import time
from channels.generic.websocket import WebsocketConsumer
from ..watchers_wss.exchange import WatcherExchange
from ..utils import DATA_FOLDER, DATA_OLD_FOLDER
from datetime import datetime
import os
from damexCommons.tools.utils import get_period_name, get_period_datetime

watcher_exchange = None

class ExchangeConsumer(WebsocketConsumer):

    def connect(self):
        self.accept()
        self.send(text_data=json.dumps({
            'type': 'connection-established',
            'message': 'You are now connected!'
        }))

    def disconnect(self, code):
        if watcher_exchange is not None:
            watcher_exchange.unsubscribe_websocket_client(self, None)

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        id = text_data_json['id']
        operation = text_data_json['operation']
        data_type = text_data_json['data_type']
        method = text_data_json['method']
        params = text_data_json['params']
        response = {
            "id": id,
            "operation": operation,
            "data_type": data_type,
            "params": params,
            "type": "old",
            "data": []
        }
        if data_type != 'prod':
            self.send(text_data=json.dumps(
                {"type": "error", "message": "data_type is not allowed!"}))
            return
        if data_type == 'prod':
            global watcher_exchange
            if watcher_exchange is None:
                watcher_exchange = WatcherExchange()
                watcher_exchange.run()
                print('WATCHER EXCHANGE INITIATED')
                
        if method != 'subscribe' and method != 'snapshot' and method != 'unsubscribe':
            self.send(text_data=json.dumps(
                {"type": "error", "message": "method is not allowed!"}))
            return
        if method == 'subscribe' or method == 'snapshot':
            if not 'market' in params and operation != 'current_values':
                self.send(text_data=json.dumps(
                    {"type": "error", "message": "market param is needed!"}))
                return
            if not 'exchange' in params:
                self.send(text_data=json.dumps(
                    {"type": "error", "message": "exchange param is needed!"}))
                return
            market = 'NONE'
            if operation != 'current_values':
                market = params['market']
            else:
                params['market'] = market
            if operation == 'ticker':
                response['data'] = []
            else:
                if not 'period' in params:
                    self.send(text_data=json.dumps(
                        {"type": "error", "message": "period param is needed!"}))
                    return
                if not 'size' in params:
                    self.send(text_data=json.dumps(
                        {"type": "error", "message": "size param is needed!"}))
                    return
                current_time = int(time.time() * 1000)
                dataset = 'snap'
                if 'current_time' in params and method == 'snapshot' and params['current_time'] is not None:
                    current_time = int(params['current_time'])
                if 'dataset' in params and (operation == 'current_orders_count' or operation == 'current_orders_amounts' or operation == 'current_orders_mid_prices'):
                    dataset = params['dataset']
                else:
                    params['dataset'] = dataset
                period = int(params['period'])
                size = int(params['size'])
                exchange = params['exchange']
                if data_type == 'prod':
                    response['data'] = add_old_prod_data(
                        operation=operation, 
                        exchange=exchange, 
                        market=market, 
                        period=period, 
                        current_time=current_time, 
                        size=size, 
                        dataset=dataset
                    )

            self.send(text_data=json.dumps(response))
        if method == 'snapshot':
            return
        self.id = id
        thread = {
            'operation': operation,
            'data_type': data_type,
            'params': params
            # 'params': dict(sorted(params.items()))
        }
        if data_type == 'prod':
            if method == 'subscribe':
                watcher_exchange.subscribe_websocket_client(self, thread)
            elif method == 'unsubscribe':
                watcher_exchange.unsubscribe_websocket_client(self, thread)

def add_old_prod_data(operation, exchange, market, period, current_time, size, dataset):
    if operation == 'current_values':
        market = 'NONE'
    final_old_data = []
    data_folder = '%s/%s/%s/%s' % (DATA_FOLDER, exchange, operation, market)
    data_folder_old = '%s/%s/%s/%s' % (DATA_OLD_FOLDER, exchange, operation, market)
    if operation == 'current_spread':
        data_folder = '%s/%s/%s/%s' % (DATA_FOLDER, exchange, 'ticker', market)
        data_folder_old = '%s/%s/%s/%s' % (DATA_OLD_FOLDER, exchange, 'ticker', market)
        
    current_datetime = datetime.fromtimestamp(int((current_time / 1e3) - (60)))
    if operation == 'current_pnl':
        current_datetime = datetime.fromtimestamp(int((current_time / 1e3) - (120)))
    period_datetime = get_period_datetime(current_datetime, period)
    i = 0
    while i < size:
        period_time = int(period_datetime.timestamp() * 1000 - (period * 60 * 1000 * i))
        data_file = data_folder + '/' + get_period_name(period) + '/' + dataset + '/' + str(period_time) + '.json'
        data_file_old = data_folder_old + '/' + get_period_name(period) + '/' + dataset + '/' + str(period_time) + '.json'
        old_data = None
        if os.path.exists(data_file):
            old_data = open(data_file, 'r', encoding='UTF-8').read()
        elif os.path.exists(data_file_old):
            old_data = open(data_file_old, 'r', encoding='UTF-8').read()
        if old_data is None:
            final_old_data.insert(0, {
                'time': period_time, 'values': []
            })
            i = i + 1
            continue
        old_data_parsed = json.loads(old_data)
        match operation:
            case 'current_orders_count' | 'current_orders_amounts' | 'current_orders_mid_prices' | 'current_values' | 'current_pnl':
                final_old_data.insert(0, old_data_parsed)
            case 'current_spread':
                values = [
                    {'operation': 'bid', 'value': old_data_parsed['bid']},
                    {'operation': 'ask', 'value': old_data_parsed['ask']},
                    {'operation': 'spread', 'value': str(float((float(old_data_parsed['ask']) - float(old_data_parsed['bid'])) / float(old_data_parsed['ask'])) * 10000)}
                ]
                final_old_data.insert(0, {
                    'time': period_time, 'values': values
                })
                    
        i = i + 1

    return final_old_data


def add_old_orders(exchange, market, data_type):
    old_orders = []
    match data_type:
        case 'prod':
            return old_orders


def add_old_balances(exchange, market, data_type):
    old_balances = []
    match data_type:
        case 'prod':
            return old_balances
