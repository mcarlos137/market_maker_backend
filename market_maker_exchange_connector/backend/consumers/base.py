import json
from channels.generic.websocket import WebsocketConsumer
from ..utils import ROUTE_OPERATIONS
from ..websocket_clients import unsubscribe_websocket_client, subscribe_websocket_client

class ConsumerBase(WebsocketConsumer):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wss_route = kwargs['wss_route']
        self.allowed_operations = kwargs['allowed_operations']
        self.add_old_data_callback = None
        self.client_id = None
        if 'add_old_data_callback' in kwargs:
            self.add_old_data_callback = kwargs['add_old_data_callback']
        
    def connect(self):
        self.accept()
        self.send(text_data=json.dumps({
            'type': 'connection-established',
            'message': 'You are now connected!'
        }))

    def disconnect(self, code):
        print('disconnect')
        unsubscribe_websocket_client(self, None)
            
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        client_id = text_data_json['id']
        operation = text_data_json['operation']
        method = text_data_json['method']
        params = text_data_json['params']
        response = {
            "id": client_id,
            "operation": operation,
            "params": params,
            "type": "old",
            "data": []
        }
                        
        if operation not in self.allowed_operations:
            self.send(text_data=json.dumps({"type": "error", "message": "operation is not allowed!"}))
            return
        
        if method != 'subscribe' and method != 'snapshot' and method != 'unsubscribe':
            self.send(text_data=json.dumps({"type": "error", "message": "method is not allowed!"}))
            return

        if 'period' in params and params['period'] not in ROUTE_OPERATIONS[self.wss_route][operation]['periods']:
            self.send(text_data=json.dumps({"type": "error", "message": "period value is not allowed!"}))
            return
        
        if 'dataset' in params and params['dataset'] not in ROUTE_OPERATIONS[self.wss_route][operation]['datasets']:
            self.send(text_data=json.dumps({"type": "error", "message": "dataset value is not allowed!"}))
            return            
        
        if method == 'subscribe' or method == 'snapshot':
            kwargs = {'operation': operation}
            for param in ROUTE_OPERATIONS[self.wss_route][operation]['params']:
                if param not in params:
                    self.send(text_data=json.dumps({"type": "error", "message": "%s param is needed!" % (param)}))
                    return
                kwargs[param] = params[param]
            if self.add_old_data_callback is not None:
                response['data'] = self.add_old_data_callback(**kwargs)
                self.send(text_data=json.dumps(response))
        
        if method == 'snapshot' or response['data'] is None:
            return
        
        self.client_id = client_id
        thread = {
            'wss_route': self.wss_route,
            'operation': operation,
            'params': params
        }        
        if method == 'subscribe':
            subscribe_websocket_client(websocket_client=self, thread=thread)
        elif method == 'unsubscribe':
            unsubscribe_websocket_client(websocket_client=self, thread=thread)

