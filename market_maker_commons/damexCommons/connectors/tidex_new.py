import json
import time
import random
import logging
from ccxt.base.exchange import Exchange as CCXTExchange
from damexCommons.connectors.ccxt import CCXTCommons
from damexCommons.connectors.base import ExchangeWSSCommons


class TidexNewCommons(CCXTCommons, ExchangeWSSCommons):
    
    def __init__(self, exchange_connector: CCXTExchange, base_asset: str, quote_asset: str):
        CCXTCommons.__init__(
            self, 
            exchange_connector=exchange_connector, 
            exchange='tidex',
            base_asset=base_asset, 
            quote_asset=quote_asset
        )
        ExchangeWSSCommons.__init__(
            self, 
            wss_url='wss://ws.tidex.com', 
            exchange='tidex', 
            wss_object_params={
                'ping': '{"method":"server.ping", "params": [], "id":%s}' % (random.randint(10000, 13000)),
                'order_book': {
                    'request': '{"method":"depth.subscribe", "params": ["%s_%s", %s, "0"], "id":%s}' % (base_asset, quote_asset, 20, random.randint(10000, 13000)),
                    'message_function': self.message_function_order_book
                },
                'ticker': {
                    'request': '{"method":"kline.subscribe", "params": ["%s_%s", 86400], "id":%s}' % (base_asset, quote_asset, random.randint(10000, 13000)),
                    'message_function': self.message_function_ticker
                }
            },
            order_book_levels=20
        )
            
    async def fetch_balance(self) -> dict:
        try:
            balance_response = self.exchange_connector.fetch_balance()
            print('balance_response', balance_response)
            balance = {}
            #for b in balance_response['info']['balances']:
            #    balance[b['asset']] = {'available': float(b['free']), 'total': float(b['free']) + float(b['locked'])}
            logging.info('balance %s', balance)
            return balance
        except Exception as e:
            raise e
        
    async def message_function_order_book(self, msg: dict) -> dict:  
        obj = json.loads(msg)
        if not 'method' in obj:
            return {}
        method = obj['method']
        if method == 'depth.update':
            if not 'asks' in obj['params'][1] or not 'bids' in obj['params'][1]:
                    return {}
            asks = [item for item in obj['params'][1]['asks'] if float(item[1]) > 0]
            bids = [item for item in obj['params'][1]['bids'] if float(item[1]) > 0]
            bids.sort(key=lambda order: float(order[0]), reverse=True)
            if len(asks) > 0 and len(bids) > 0:
                order_book_time = int(time.time() * 1000)
                return {
                    'time': order_book_time,
                    'asks': asks,
                    'bids': bids,
                }        
        return {}

    async def message_function_ticker(self, msg: str) -> dict:
        obj = json.loads(msg)
        if not 'method' in obj:
            return {}
        method = obj['method']
        if method == 'kline.update':
            values = str(obj['params'])[1:][:-1][1:][:-1].replace("'", "").split(', ')
            if len(values) < 8:
                return {}
            ticker_time = int(time.time() * 1000)
            return {
                'time': ticker_time,
                'lastPrice': float(values[2]),
                'volume': float(values[6]),
                'high': float(values[3]),
                'low': float(values[4]),
            }
        return {}