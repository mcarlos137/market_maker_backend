import time
import threading
from damexCommons.tools.dbs import get_exchange_db
from ..websocket_clients import WEBSOCKET_CLIENTS
from ..utils import ROUTE_OPERATIONS

exchange_db = get_exchange_db(db_connection='exchange_connector')

class NotifierWssBase:
    
    def __init__(self, wss_route: str, notifier_id: str, callback: callable) -> None:
        self.wss_route = wss_route
        self.notifier_id = notifier_id
        self.callback = callback
        
    def run(self) -> None:
        thread = threading.Thread(target=self.db_listen)
        thread.start()
    
    def db_listen(self) -> None:
        while True:
            try:
                exchange_db.db_listen(notifier=self.notifier_id, callback=self.notifier_callback)
            except Exception as e:
                print('error', e)
            time.sleep(10)
            print('retrying notify_order_book_damexusdt')
                    
    def notifier_callback(self, data: dict) -> None:
        websocket_clients_to_send = {}
        for websocket_client in WEBSOCKET_CLIENTS:
            for thread in websocket_client[1]:
                wss_route = thread['wss_route']
                if self.wss_route != wss_route:
                    continue
                operation = thread['operation']
                params = thread['params']
                if operation not in ROUTE_OPERATIONS[self.wss_route]:
                    continue
                if len(ROUTE_OPERATIONS[self.wss_route][operation]['params']) != len(params):
                    continue
                if ROUTE_OPERATIONS[self.wss_route][operation]['folders'] is not None:
                    continue
                websocket_clients_to_send[websocket_client[0].client_id] = [websocket_client[0], params, operation]
        self.callback(data, websocket_clients_to_send)
        