import os
import json
from damexCommons.tools.exchange_db import ExchangeDB
from ..utils import DATA_FOLDER, ROUTE_OPERATIONS
from .base import WatcherWssBase

exchange_db = ExchangeDB(db_connection='exchange_connector')

WSS_ROUTE = 'current_spread'

class WatcherWssCurrentSpread(WatcherWssBase):
    
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
                        #folders_to_watch.add(folder_to_watch)
                        for period in ROUTE_OPERATIONS[WSS_ROUTE][operation]['periods']:
                            for dataset in ROUTE_OPERATIONS[WSS_ROUTE][operation]['datasets']:
                                folder_to_watch = '%s/%s/%s/%s/%s/%s' % (DATA_FOLDER, exchange, folder, market, period, dataset)
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
            for websocket_client_id in websocket_clients_to_send:
                operation = websocket_clients_to_send[websocket_client_id][2]
                match operation:
                    case 'get':
                        values = [
                            {'operation': 'bid', 'value': parsed_data['bids'][0][0]},
                            {'operation': 'ask', 'value': parsed_data['asks'][0][0]},
                            {'operation': 'spread', 'value': str(float((float(parsed_data['asks'][0][0]) - float(parsed_data['bids'][0][0])) / float(parsed_data['asks'][0][0])) * 10000)}   
                        ]
                        response = {
                            'id': websocket_client_id,
                            'operation': operation,
                            'params': websocket_clients_to_send[websocket_client_id][1],
                            'type': 'new',
                            'data': [{'time': parsed_data['time'], 'values': values}]
                        }
                        websocket_clients_to_send[websocket_client_id][0].send(text_data=json.dumps(response))
        except Exception as e:
            print('problem retrieving data', e)