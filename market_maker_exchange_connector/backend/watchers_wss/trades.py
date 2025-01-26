import os
import json
from damexCommons.tools.exchange_db import ExchangeDB
from ..utils import DATA_FOLDER, ROUTE_OPERATIONS
from .base import WatcherWssBase

exchange_db = ExchangeDB(db_connection='exchange_connector')

WSS_ROUTE = 'trades'

class WatcherWssTrades(WatcherWssBase):
    
    def __init__(self):
        folders_to_watch = set()
        exchanges_info = exchange_db.fetch_exchanges_info_db()
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
 
        folder_to_watch = '%s/%s/%s/%s' % (DATA_FOLDER, 'APP', WSS_ROUTE, 'DAMEX-USDT')
        print('------------->', folder_to_watch)
        if os.path.exists(folder_to_watch):
            folders_to_watch.add(folder_to_watch)
        super().__init__(WSS_ROUTE, folders_to_watch=folders_to_watch, callback=self.callback)


    def callback(self, src_path: str, websocket_clients_to_send):
        try:
            data = open(src_path, 'r', encoding='UTF-8').read()
            parsed_data = json.loads(data)
            if 'timestamp' not in parsed_data:
                raise Exception
            for websocket_client_id in websocket_clients_to_send:
                operation = websocket_clients_to_send[websocket_client_id][2]
                match operation:
                    case 'fetch':
                        response = {
                            'id': websocket_client_id,
                            'operation': operation,
                            'params': websocket_clients_to_send[websocket_client_id][1],
                            'type': 'new',
                            'data': [parsed_data]
                        }
                        websocket_clients_to_send[websocket_client_id][0].send(text_data=json.dumps(response))
        except Exception as e:
            print('problem retrieving data', e)