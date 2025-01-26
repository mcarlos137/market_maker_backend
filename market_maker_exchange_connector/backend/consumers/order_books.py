import asyncio
import time
import json
import threading
from damexCommons.tools.dbs import get_exchange_db
from damexCommons.tools.exchange import get_order_book_price
from ..notifiers_wss.order_books import NotifierWssOrderBooks
from .base import ConsumerBase
from ..websocket_clients import WEBSOCKET_CLIENTS

WSS_ROUTE = 'order_books'
ALLOWED_OPERATIONS = ['fetch', 'get_price']

notifier_wss_order_books = None

time_thread_initiated = False

exchange_db = get_exchange_db(db_connection='exchange_connector')

class ConsumerOrderBooks(ConsumerBase):
    
    def __init__(self, *args, **kwargs):
        kwargs['wss_route'] = WSS_ROUTE
        kwargs['allowed_operations'] = ALLOWED_OPERATIONS
        global notifier_wss_order_books
        if notifier_wss_order_books is None:
            notifier_wss_order_books = NotifierWssOrderBooks()
            notifier_wss_order_books.run()
            print('notifier wss %s initiated' % (WSS_ROUTE))
        global time_thread_initiated
        if not time_thread_initiated:
            time_thread_initiated = True
            time_thread = threading.Thread(target=self.time_thread)
            time_thread.start()
        kwargs['add_old_data_callback'] = self.add_old_data_callback
        super().__init__(*args, **kwargs)
                
        
    def add_old_data_callback(self, *args, **kwargs):
        match kwargs['operation']:
            case 'fetch':        
                market = kwargs['market']
                size = kwargs['size']
                return asyncio.run(exchange_db.get_order_book_db(base_asset=market.split('-')[0], quote_asset=market.split('-')[1], size=size))    
            case 'get_price':
                market = kwargs['market']
                currency = kwargs['currency']
                side = kwargs['side']
                amount = kwargs['amount']
                return asyncio.run(get_order_book_price(base_asset=market.split('-')[0], quote_asset=market.split('-')[1], currency=currency, side=side, amount=amount))
                    
        
    def time_thread(self) -> None:
        while True:
            try:
                buy_price = asyncio.run(get_order_book_price(base_asset='DAMEX', quote_asset='USDT', currency='USDT', side='buy', amount=0))
                sell_price = asyncio.run(get_order_book_price(base_asset='DAMEX', quote_asset='USDT', currency='USDT', side='sell', amount=0))
                for websocket_client in WEBSOCKET_CLIENTS:
                    for thread in websocket_client[1]:
                        params = thread['params']
                        operation = thread['operation']
                        if operation != 'get_price':
                            continue
                        if params['market'] != 'DAMEX-USDT':
                            continue
                        if params['currency'] not in ['DAMEX', 'USDT']:
                            continue
                        response = {
                            'id': websocket_client[0].client_id,
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
