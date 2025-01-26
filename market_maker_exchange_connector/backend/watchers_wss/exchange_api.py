import json
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from damexCommons.tools.exchange_db import ExchangeDB
from ..utils import DATA_FOLDER, DATA_OLD_FOLDER

exchange_db = ExchangeDB(db_connection='exchange_connector')

OPERATIONS = ['trades', 'ticker', 'order_books']

LAST_DATA = {
    'market_info': None
}

class WatcherExchangeAPI:

    def __init__(self):
        self.observer = Observer()
        self.websocket_clients = []

    def run(self):
        print('ADDING WATCHERS EXCHANGE API')
        threads = []
        directories_to_watch = set()
        exchanges_info = exchange_db.fetch_exchanges_info_db()
        for exchange in exchanges_info:
            for market in exchanges_info[exchange]:                
                market_use = exchanges_info[exchange][market]['market_use']
                if market_use != 'mm':
                    continue
                for operation in OPERATIONS:
                    directory_to_watch = '%s/%s/%s/%s' % (DATA_FOLDER, exchange, operation, market)
                    if not os.path.exists(directory_to_watch):
                        continue
                    print('------------->', directory_to_watch)
                    directories_to_watch.add(directory_to_watch)
 
        for operation in OPERATIONS:
            directory_to_watch = '%s/%s/%s/%s' % (DATA_FOLDER, 'APP', operation, 'DAMEX-USDT')
            print('------------->', directory_to_watch)
            if not os.path.exists(directory_to_watch):
                continue
            directories_to_watch.add(directory_to_watch)
        
        for directory_to_watch in directories_to_watch:
            event_handler = Handler(self.websocket_clients)
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
        print('EXCHANGE API SUBSCRIBE WEBSOCKET CLIENT')

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
                        if ws_client[1][i]['operation'] == thread['operation'] and ws_client[1][i]['params'] == thread['params']:
                            ws_client[1].pop(i)
                            break
                        i = i + 1
                break
        print('EXCHANGE API UNSUBSCRIBE WEBSOCKET CLIENT')


class Handler(FileSystemEventHandler):

    def __init__(self, websocket_clients):
        self.websocket_clients = websocket_clients

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
                        market = params['market']
                        if 'info.json' in event.src_path:
                            continue
                        match operation:
                            case 'trades':
                                if market in event.src_path and operation in event.src_path:
                                    try:
                                        data = open(event.src_path, 'r', encoding='UTF-8').read()
                                        parsed_data = json.loads(data)
                                        if 'timestamp' not in parsed_data:
                                            raise Exception
                                        response = {
                                            'id': websocket_client[0].id,
                                            'operation': operation,
                                            'params': params,
                                            'type': 'new',
                                            'data': [parsed_data]
                                        }
                                        websocket_client[0].send(text_data=json.dumps(response))
                                    except Exception as e:
                                        print('PROBLEM AT TRY TO RETRIEVE DATA', e)
                                        
                                        
                            case 'market_info':
                                if market in event.src_path and ('ticker' in event.src_path or 'order_books' in event.src_path):
                                    exchange = event.src_path.split('/')[2]
                                    print('--------------->', event.src_path)
                                    try:
                                        data = open(event.src_path, 'r', encoding='UTF-8').read()
                                        parsed_data = json.loads(data)
                                        if 'time' not in parsed_data:
                                            raise Exception
                                        new_parsed_data = {}
                                        if 'ticker' in event.src_path:
                                            new_parsed_data = parsed_data.copy()
                                            new_parsed_data['exchange'] = exchange
                                            base_folder = '%s/%s/%s/%s/' % (DATA_FOLDER, exchange, 'order_books', market)
                                            last_file_name = json.loads(open(base_folder + 'info.json', 'r', encoding='UTF-8').read())['last_file_name']
                                            order_book = json.loads(open(base_folder + last_file_name, 'r', encoding='UTF-8').read())
                                            new_parsed_data['time'] = order_book['time']
                                            new_parsed_data['spread'] = str(float((float(order_book['asks'][0][0]) - float(order_book['bids'][0][0])) / float(order_book['asks'][0][0])) * 10000)
                                        if 'order_books' in event.src_path:
                                            new_parsed_data['exchange'] = exchange
                                            base_folder = '%s/%s/%s/%s/' % (DATA_FOLDER, exchange, 'ticker', market)
                                            last_file_name = json.loads(open(base_folder + 'info.json', 'r', encoding='UTF-8').read())['last_file_name']
                                            last_ticker_file = base_folder + last_file_name
                                            if not os.path.exists(base_folder + last_file_name):
                                                last_ticker_file = '%s/%s/%s/%s/' % (DATA_OLD_FOLDER, exchange, 'ticker', market) + last_file_name
                                            ticker = json.loads(open(last_ticker_file, 'r', encoding='UTF-8').read())
                                            new_parsed_data['time'] = ticker['time']
                                            new_parsed_data['lastPrice'] = ticker['lastPrice']
                                            new_parsed_data['volume'] = ticker['volume']
                                            new_parsed_data['high'] = ticker['high']
                                            new_parsed_data['low'] = ticker['low']
                                            new_parsed_data['spread'] = str(float((float(parsed_data['asks'][0][0]) - float(parsed_data['bids'][0][0])) / float(parsed_data['asks'][0][0])) * 10000)                                            
                                            
                                        if LAST_DATA['market_info'] is not None:
                                            new_parsed_data_to_compare = new_parsed_data.copy()
                                            del new_parsed_data_to_compare['time']
                                            last_data_to_compare =  LAST_DATA['market_info'].copy()
                                            del last_data_to_compare['time']
                                            if new_parsed_data_to_compare == last_data_to_compare:
                                                return
                                        LAST_DATA['market_info'] = new_parsed_data
                                        response = {
                                            'id': websocket_client[0].id,
                                            'operation': operation,
                                            'params': thread['params'],
                                            'type': 'new',
                                            'data': [new_parsed_data]
                                        }
                                        websocket_client[0].send(text_data=json.dumps(response))
                                    except Exception as e:
                                        print('PROBLEM AT TRY TO RETRIEVE DATA', e)
                                                                                
                                        
            except Exception as e:
                print('PROBLEM AT TRY TO RETRIEVE DATA', e)
