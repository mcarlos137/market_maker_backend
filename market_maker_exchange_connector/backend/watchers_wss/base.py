from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ..websocket_clients import WEBSOCKET_CLIENTS
from ..utils import ROUTE_OPERATIONS

class WatcherWssBase:

    def __init__(self, wss_route: str, folders_to_watch: set[str], callback: callable):
        self.wss_route = wss_route
        self.folders_to_watch = folders_to_watch
        self.callback = callback
        self.observer = Observer()

    def run(self):
        print('adding watchers %s' % (self.wss_route))
        
        for folder_to_watch in self.folders_to_watch:
            event_handler = Handler(self.wss_route, self.callback)
            self.observer.schedule(event_handler, folder_to_watch, recursive=False)
                            
        self.observer.start()


class Handler(FileSystemEventHandler):

    def __init__(self, wss_route: str, callback: callable):
        self.wss_route = wss_route
        self.callback = callback

    def on_any_event(self, event):
        if event.is_directory or 'info.json' in event.src_path:
            return
        elif event.event_type == 'created':
            try:
                websocket_clients_to_send = {}         
                for websocket_client in WEBSOCKET_CLIENTS:
                    for thread in websocket_client[1]:
                        wss_route = thread['wss_route']
                        if self.wss_route != wss_route:
                            continue
                        operation = thread['operation']
                        params = thread['params']
                        if 'exchange' in params and params['exchange'] not in event.src_path:
                            continue
                        if 'market' in params and params['market'] not in event.src_path:
                            continue
                        if 'period' in params and params['period'] not in event.src_path:
                            continue
                        if 'dataset' in params and params['dataset'] not in event.src_path:
                            continue
                        if operation not in ROUTE_OPERATIONS[self.wss_route]:
                            continue
                        if len(ROUTE_OPERATIONS[self.wss_route][operation]['params']) != len(params):
                            continue
                        if ROUTE_OPERATIONS[self.wss_route][operation]['folders'] is not None and event.src_path.split('/')[3] not in ROUTE_OPERATIONS[self.wss_route][operation]['folders']:
                            continue
                        websocket_clients_to_send[websocket_client[0].client_id] = [websocket_client[0], params, operation]
                if len(websocket_clients_to_send) == 0:
                    return
                self.callback(event.src_path, websocket_clients_to_send)
                                                                                                                        
            except Exception as e:
                print('problem at retrieving data', e)
