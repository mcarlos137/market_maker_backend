from ccxt.base.exchange import Exchange as CCXTExchange
import logging
import time
import gzip
import random
import json
from damexCommons.connectors.base import ExchangeWSSCommons
from damexCommons.connectors.ccxt import CCXTCommons
from damexCommons.tools.exchange import match_trade_order

class CryptocomCommons(CCXTCommons, ExchangeWSSCommons):
    
    def __init__(self, exchange_connector: CCXTExchange, base_asset: str, quote_asset: str):
        CCXTCommons.__init__(
            self, 
            exchange_connector=exchange_connector, 
            exchange='cryptocom',
            base_asset=base_asset, 
            quote_asset=quote_asset
        )        
        ExchangeWSSCommons.__init__(
            self, 
            wss_url='wss://stream.crypto.com/exchange/v1/market', 
            exchange='cryptocom', 
            wss_object_params={
                'order_book': {
                    'request': '{"id": %s, "method": "subscribe", "params": {"channels": ["book.%s_%s"]}}' % (random.randint(100000, 130000), base_asset.upper(), quote_asset.upper()),
                    'message_function': self.message_function_order_book
                },
                'ticker': {
                    'request': '{"id": %s, "method": "subscribe", "params": {"channels": ["ticker.%s_%s"]}}' % (random.randint(100000, 130000), base_asset.upper(), quote_asset.upper()),
                    'message_function': self.message_function_ticker
                },
                'trade': {
                    'request': '{"id": %s, "method": "subscribe", "params": {"channels": ["trade.%s_%s"]}}' % (random.randint(100000, 130000), base_asset.upper(), quote_asset.upper()),
                    'message_function': self.message_function_trade
                },
            },
            order_book_levels=20
        )
        
    async def fetch_balance(self) -> dict:
       raise NotImplementedError
    
    async def message_function_order_book(self, msg: str) -> dict:
        obj = json.loads(msg)
        if obj['method'] == 'public/heartbeat':
            self.wss.send('{"id": %s, "method": "public/respond-heartbeat"}' % (obj['id']))
            return {}
        if 'result' in obj and obj['result']['channel'] == 'book':
            values = obj['result']['data'][0]
            return {
                'time': int(values['t']),
                'asks': values['asks'][:20],
                'bids': values['bids'][:20],
            }        
        return {}
    
    async def message_function_ticker(self, msg: str) -> dict:
        obj = json.loads(msg)
        if obj['method'] == 'public/heartbeat':
            self.wss.send('{"id": %s, "method": "public/respond-heartbeat"}' % (obj['id']))
            return {}
        if 'result' in obj and obj['result']['channel'] == 'ticker':
            values = obj['result']['data'][0]
            return {
                'time': int(time.time() * 1000),
                'lastPrice': float(values['a']),
                'volume': float(values['vv']),
                'high': float(values['h']),
                'low': float(values['l']),
            }
        return {}
    
    async def message_function_trade(self, msg: str) -> dict:
        obj = json.loads(msg)
        data = {}
        if obj['method'] == 'public/heartbeat':
            self.wss.send('{"id": %s, "method": "public/respond-heartbeat"}' % (obj['id']))
            return {}
        if 'result' in obj and obj['result']['channel'] == 'trade':
            values = obj['result']['data'][0]
            data['time'] = int(values['t'])
            data['price'] = float(values['p'])
            data['amount'] = float(values['q'])
            data['currency'] = self.base_asset
            data['side'] = str(values['s']).upper()
            data['exchange'] = self.exchange                
        #    price = data['price']
        #    amount = data['amount']
        #    time.sleep(5)
        #    match_to = await match_trade_order(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, price=price, amount=amount, trade_side=data['side'].upper())
        #    data.update(match_to)
            return data
        return data
