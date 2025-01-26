import os
import json
from damexCommons.tools.exchange_db import ExchangeDB
from ..utils import DATA_FOLDER, DATA_OLD_FOLDER, ROUTE_OPERATIONS
from .base import WatcherWssBase

exchange_db = ExchangeDB(db_connection='exchange_connector')

WSS_ROUTE = 'market_info'

class WatcherWssMarketInfo(WatcherWssBase):
    
    def __init__(self):
        folders_to_watch = set()
        exchanges_info = exchange_db.fetch_exchanges_info_db()
        self.last_data = None
        for exchange in exchanges_info:
            for market in exchanges_info[exchange]:                
                market_use = exchanges_info[exchange][market]['market_use']
                if market_use != 'mm':
                    continue
                for operation in ROUTE_OPERATIONS[WSS_ROUTE]:
                    for folder in ROUTE_OPERATIONS[WSS_ROUTE][operation]['folders']:
                        folder_to_watch = '%s/%s/%s/%s' % (DATA_FOLDER, exchange, folder, market)
                        if not os.path.exists(folder_to_watch):
                            continue
                        print('------------->', folder_to_watch)
                        folders_to_watch.add(folder_to_watch)
 
        super().__init__(WSS_ROUTE, folders_to_watch=folders_to_watch, callback=self.callback)


    def callback(self, src_path: str, websocket_clients_to_send):
        try:
            data = open(src_path, 'r', encoding='UTF-8').read()
            parsed_data = json.loads(data)
            if 'time' not in parsed_data:
                raise Exception
            new_parsed_data = {}
            exchange = src_path.split('/')[2]
            market = src_path.split('/')[4]
            if 'ticker' in src_path:
                new_parsed_data = parsed_data.copy()
                new_parsed_data['exchange'] = exchange
                base_folder = '%s/%s/%s/%s/' % (DATA_FOLDER, exchange, 'order_books', market)
                last_file_name = json.loads(open(base_folder + 'info.json', 'r', encoding='UTF-8').read())['last_file_name']
                order_book = json.loads(open(base_folder + last_file_name, 'r', encoding='UTF-8').read())
                new_parsed_data['time'] = order_book['time']
                new_parsed_data['spread'] = str(float((float(order_book['asks'][0][0]) - float(order_book['bids'][0][0])) / float(order_book['asks'][0][0])) * 10000)
            if 'order_books' in src_path:
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
                if 'high' in ticker:
                    new_parsed_data['high'] = ticker['high']
                elif 'hign' in ticker:
                    new_parsed_data['high'] = ticker['hign']
                new_parsed_data['low'] = ticker['low']
                new_parsed_data['spread'] = str(float((float(parsed_data['asks'][0][0]) - float(parsed_data['bids'][0][0])) / float(parsed_data['asks'][0][0])) * 10000)                                            
            if self.last_data is not None and exchange in self.last_data:
                new_parsed_data_to_compare = new_parsed_data.copy()
                del new_parsed_data_to_compare['time']
                last_data_to_compare =  self.last_data[exchange].copy()
                del last_data_to_compare['time']
                if new_parsed_data_to_compare == last_data_to_compare:
                    return
            if self.last_data is None:
                self.last_data = {}
            if exchange not in self.last_data:
                self.last_data[exchange] = {}            
            self.last_data[exchange] = new_parsed_data
                        
            for websocket_client_id in websocket_clients_to_send:
                operation = websocket_clients_to_send[websocket_client_id][2]
                match operation:
                    case 'get':
                        response = {
                            'id': websocket_client_id,
                            'operation': operation,
                            'params': websocket_clients_to_send[websocket_client_id][1],
                            'type': 'new',
                            'data': [new_parsed_data]
                        }
                        websocket_clients_to_send[websocket_client_id][0].send(text_data=json.dumps(response))
        except Exception as e:
            print('problem retrieving data', e)