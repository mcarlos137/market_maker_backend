import os
import json
from ..utils import DATA_FOLDER, ROUTE_OPERATIONS
from .base import WatcherWssBase

WSS_ROUTE = 'current_values'
EXCHANGES = ['ascendex', 'bitmart', 'coinstore', 'mexc', 'tidex']

class WatcherWssCurrentValues(WatcherWssBase):
    
    def __init__(self):
        folders_to_watch = set()
        self.last_data = None
        for exchange in EXCHANGES:
            for operation in ROUTE_OPERATIONS[WSS_ROUTE]:
                for folder in ROUTE_OPERATIONS[WSS_ROUTE][operation]['folders']:
                    folder_to_watch = '%s/%s/%s/%s' % (DATA_FOLDER, exchange, folder, 'NONE')
                    if not os.path.exists(folder_to_watch):
                        continue
                    #folders_to_watch.add(folder_to_watch)
                    for period in ROUTE_OPERATIONS[WSS_ROUTE][operation]['periods']:
                        for dataset in ROUTE_OPERATIONS[WSS_ROUTE][operation]['datasets']:
                            folder_to_watch = '%s/%s/%s/%s/%s/%s' % (DATA_FOLDER, exchange, folder, 'NONE', period, dataset)
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