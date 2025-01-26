import json
import time
import threading
import asyncio
from damexCommons.tools.dbs import get_exchange_db
from damexCommons.tools.exchange import get_order_book_price

exchange_db = get_exchange_db(db_connection='exchange_connector')

class NotifierExchangeAPI:

    def __init__(self):
        self.websocket_clients = []
        
    def run(self) -> None:
        thread_order_book_damexusdt = threading.Thread(target=self.db_listen)
        thread_order_book_damexusdt.start()
        time_thread = threading.Thread(target=self.time_thread)
        time_thread.start()
    
    def db_listen(self) -> None:
        while True:
            try:
                exchange_db.db_listen(notifier='notify_order_book_damexusdt', callback=self.order_book_callback)
            except Exception as e:
                print('error', e)
            time.sleep(10)
            print('retrying notify_order_book_damexusdt')
            
    def time_thread(self) -> None:
        while True:
            try:
                buy_price = asyncio.run(get_order_book_price(base_asset='DAMEX', quote_asset='USDT', currency='USDT', side='buy', amount=0))
                sell_price = asyncio.run(get_order_book_price(base_asset='DAMEX', quote_asset='USDT', currency='USDT', side='sell', amount=0))
                for websocket_client in self.websocket_clients:
                    for thread in websocket_client[1]:
                        params = thread['params']
                        operation = thread['operation']
                        if operation != 'order_book_price':
                            continue
                        if params['market'] != 'DAMEX-USDT':
                            continue
                        if params['currency'] not in ['DAMEX', 'USDT']:
                            continue
                        response = {
                            'id': websocket_client[0].id,
                            'operation': operation,
                            'params': params,
                            'type': 'new',
                            'data': buy_price if params['side'] == 'buy' else sell_price
                        }
                        print('response', response)
                        websocket_client[0].send(text_data=json.dumps(response))
            except Exception as e:
                print('error', e)
            time.sleep(10)
            
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
        
    def order_book_callback(self, order_book: dict) -> None:
        for websocket_client in self.websocket_clients:
            for thread in websocket_client[1]:
                try:
                    params = thread['params']
                    operation = thread['operation']
                    match operation:
                        case 'order_book':                        
                            size = params['size']
                            order_book['asks'] = order_book['asks'][0:size]
                            order_book['bids'] = order_book['bids'][0:size]
                            response = {
                                'id': websocket_client[0].id,
                                'operation': operation,
                                'params': params,
                                'type': 'new',
                                'data': order_book
                            }
                            websocket_client[0].send(text_data=json.dumps(response))
                        case 'order_book_price':                   
                            market = params['market']
                            amount = params['amount']
                            currency = params['currency']
                            side = params['side']
                            market_components = market.split('-')
                            amount_left = amount
                            amount_by_price_sum = 0
                            if len(order_book['bids']) == 0 and len(order_book['asks']) == 0 :
                                get_price_data = {'price': None, 'amount': 0}   
                            if len(order_book['bids']) == 0 and len(order_book['asks']) > 0 and side == 'sell':
                                get_price_data = {'price': order_book['asks'][0][0] * 0.95, 'amount': 0}
                            elif len(order_book['asks']) == 0 and len(order_book['bids']) > 0 and side == 'buy':
                                get_price_data = {'price': order_book['bids'][0][0] * 1.05, 'amount': 0}
                            else:
                                for o in  order_book['bids' if side == 'sell' else 'asks']:  
                                    var = None
                                    if market_components[0] == currency:
                                        var = o[1]
                                    elif market_components[1] == currency:
                                        var = o[0] * o[1]
                                    if var >= amount_left:
                                        amount_by_price_sum += o[0] * amount_left
                                        amount_left = 0
                                        break 
                                    else:
                                        amount_by_price_sum += o[0] * var
                                        amount_left = amount_left - var
                                amount_new = amount - amount_left
                                if amount_new == 0:
                                    get_price_data = {'price': None, 'amount': 0}
                                else:
                                    price = amount_by_price_sum / amount_new
                                    if side == 'sell' and len(order_book['asks']) > 0:
                                        ask_lowest_price = order_book['asks'][0][0]
                                        if float(price) > float(ask_lowest_price):
                                            price = ask_lowest_price
                                    get_price_data = {'price': price, 'amount': amount_new}
                                    
                                    #dayly_limit_buy_amount = 200000
                                    #dayly_limit_sell_amount = 100000
                                        
                            response = {
                                'id': websocket_client[0].id,
                                'operation': operation,
                                'params': params,
                                'type': 'new',
                                'data': get_price_data
                            }
                            websocket_client[0].send(text_data=json.dumps(response))

                except Exception as e:
                    print('ERROR AT PROCESSING', e)
        