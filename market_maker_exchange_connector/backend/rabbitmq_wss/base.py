import pika
import json
import threading
from ..websocket_clients import WEBSOCKET_CLIENTS
from ..utils import ROUTE_OPERATIONS

class RabbitmqWssBase:

    def __init__(self, wss_route: str, callback: callable):
        self.wss_route = wss_route
        self.callback = callback
        self.queue_connection = pika.BlockingConnection(
            pika.ConnectionParameters('market_maker_rabbitmq',
                5672,
                '/',
                pika.PlainCredentials('guest', 'guest')
            )
        )
        self.queue_channel = self.queue_connection.channel()
        
    def run(self):
        consumer_thread = threading.Thread(target=self.consumer_thread)
        consumer_thread.start()
        
    def consumer_thread(self):
        self.queue_channel.basic_consume(queue='arbitrage_opportunity.simple',
            auto_ack=True,
            on_message_callback=self.message_callback
        )
        self.queue_channel.start_consuming()

    def message_callback(self, ch, method, properties, body):
        body_json = json.loads(body)
        try:
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
                    websocket_clients_to_send[websocket_client[0].client_id] = [websocket_client[0], params, operation]
            if len(websocket_clients_to_send) == 0:
                return
            self.callback(body_json, websocket_clients_to_send)
                                                                                                                        
        except Exception as e:
            print('problem at retrieving data', e)
