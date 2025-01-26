import json
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ..utils import DATA_FOLDER
from damexCommons.tools.utils import get_period_name, OPERATIONS_DATA_TYPES, PERIODS
from damexCommons.tools.exchange_db import ExchangeDB

exchange_db = ExchangeDB(db_connection='exchange_connector')

class WatcherExchange:

    def __init__(self):
        self.observer = Observer()
        self.websocket_clients = []
        self.operations_last_time = {}

    def run(self):
        print('ADDING WATCHERS EXCHANGE')
        threads = []
        directories_to_watch = set()
        exchanges_info = exchange_db.fetch_exchanges_info_db()
        for exchange in exchanges_info:
            for market in exchanges_info[exchange]:                
                market_use = exchanges_info[exchange][market]['market_use']
                if market_use != 'mm':
                    continue
                for operation in OPERATIONS_DATA_TYPES:
                    if operation == 'ticker' and 'paper_trade' in exchange:
                        continue
                    for period in PERIODS:
                        for dataset in OPERATIONS_DATA_TYPES[operation]:
                            if operation == 'current_values':
                                market = 'NONE'
                            directory_to_watch = '%s/%s/%s/%s/%s/%s' % (DATA_FOLDER, exchange, operation, market, period, dataset)
                            if not os.path.exists(directory_to_watch):
                                continue
                            directories_to_watch.add(directory_to_watch)
                        continue
                                
        for directory_to_watch in directories_to_watch:
            print(directory_to_watch)
            event_handler = Handler(self.websocket_clients, self.operations_last_time)
            self.observer.schedule(event_handler, directory_to_watch, recursive=False)
            threads.append(self.observer)
            
        self.observer.start()

    def subscribe_websocket_client(self, websocket_client, thread):
        ws_client_founded = False
        for ws_client in self.websocket_clients:
            if websocket_client.id == ws_client[0].id:
                ws_client[1].append(thread)
                ws_client_founded = True
                break
        if not ws_client_founded:
            self.websocket_clients.append([websocket_client, [thread]])
        print('EXCHANGE SUBSCRIBE WEBSOCKET CLIENT')

    def unsubscribe_websocket_client(self, websocket_client, thread):
        for ws_client in self.websocket_clients[:]:
            if not hasattr(websocket_client, 'id'):
                continue
            if ws_client[0].id == websocket_client.id:
                if thread is None:
                    self.websocket_clients.remove(ws_client)
                else:
                    i = 0
                    while i < len(ws_client[1]):
                        if ws_client[1][i]['operation'] == thread['operation'] and ws_client[1][i]['data_type'] == thread['data_type'] and ws_client[1][i]['params'] == thread['params']:
                            ws_client[1].pop(i)
                            break
                        i = i + 1
                break
        print('EXCHANGE UNSUBSCRIBE WEBSOCKET CLIENT')


class Handler(FileSystemEventHandler):

    def __init__(self, websocket_clients, operations_last_time):
        self.websocket_clients = websocket_clients
        self.operations_last_time = operations_last_time

    def on_any_event(self, event):
        if event.is_directory:
            return None

        elif event.event_type == 'created':
            # Take any action here when a file is first created.
            data = ''
            try:
                for websocket_client in self.websocket_clients:
                    for thread in websocket_client[1]:
                        params = thread['params']
                        operation = thread['operation']
                        operation_path = operation
                        if operation == 'current_spread':
                            operation_path = 'order_books'
                        exchange_path = '/' + params['exchange'] + '/'  
                        market = params['market']
                        period = get_period_name(int(params['period']))
                        dataset = params['dataset']
                        match operation:
                            case 'current_orders_count' | 'current_orders_amounts' | 'current_orders_mid_prices' | 'current_values' | 'current_pnl' | 'ticker':
                                if exchange_path in event.src_path and market in event.src_path and operation_path in event.src_path and period in event.src_path and dataset in event.src_path:
                                    try:
                                        data = open(event.src_path, 'r', encoding='UTF-8').read()
                                        parsed_data = json.loads(data)
                                        if 'time' not in parsed_data:
                                            raise Exception
                                        response = {
                                            'id': websocket_client[0].id,
                                            'operation': operation,
                                            'data_type': thread['data_type'],
                                            'params': thread['params'],
                                            'type': 'new',
                                            'data': [parsed_data]
                                        }
                                        websocket_client[0].send(text_data=json.dumps(response))
                                    except Exception as e:
                                        print('PROBLEM AT TRY TO RETRIEVE DATA', e)
                                    
                            case 'current_spread':
                                if exchange_path in event.src_path and market in event.src_path and operation_path in event.src_path and period in event.src_path and dataset in event.src_path:
                                    try:
                                        data = open(event.src_path, 'r', encoding='UTF-8').read()
                                        parsed_data = json.loads(data)
                                        if 'time' not in parsed_data:
                                            raise Exception
                                        parsed_data = json.loads(data)
                                        values = [
                                            {'operation': 'bid', 'value': parsed_data['bid']},
                                            {'operation': 'ask', 'value': parsed_data['ask']},
                                            {'operation': 'spread', 'value': str(float((float(parsed_data['ask']) - float(parsed_data['bid'])) / float(parsed_data['ask'])) * 10000)}   
                                        ]
                                        data = {'time': parsed_data['time'], 'values': values}
                                        response = {
                                            'id': websocket_client[0].id,
                                            'operation': operation,
                                            'data_type': thread['data_type'],
                                            'params': thread['params'],
                                            'type': 'new',
                                            'data': [data]
                                        }
                                        websocket_client[0].send(text_data=json.dumps(response))
                                    except Exception as e:
                                        print('PROBLEM AT TRY TO RETRIEVE DATA', e)
                                        
            except Exception as e:
                print('PROBLEM AT TRY TO RETRIEVE DATA', e)
