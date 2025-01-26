from ccxt.base.exchange import Exchange as CCXTExchange
import logging
import time
import json
from damexCommons.connectors.base import ExchangeCommons, ExchangeWSSCommons
from damexCommons.tools.exchange import match_trade_order

class LmaxCommons(ExchangeCommons, ExchangeWSSCommons):
    
    def __init__(self, api_key: str, api_secret: str, base_asset: str, quote_asset: str):
        ExchangeCommons.__init__(
            self,
            exchange_connector=None,
            exchange='lmax',
            base_asset=base_asset,
            quote_asset=quote_asset
        )
        ExchangeWSSCommons.__init__(
            self, 
            wss_url='wss://public-data-api.london-digital.lmax.com/v1/web-socket', 
            exchange='lmax', 
            wss_object_params={
                'order_book': {
                    'request': '{"type": "SUBSCRIBE", "channels": [{"name": "ORDER_BOOK", "instruments": ["%s-%s"]}]}' % (base_asset.lower(), quote_asset.lower()),
                    'message_function': self.message_function_order_book
                },
            },
            order_book_levels=20
        )
        self.api_key = api_key
        self.api_secret = api_secret
    
    @property
    def exchange_pair(self) -> str:
        return self.base_asset + '_' + self.quote_asset
        
    async def fetch_balance(self) -> dict:
       raise NotImplementedError
    
    async def message_function_order_book(self, msg: str) -> dict:
        obj = json.loads(msg)
        order_book = {'asks': [], 'bids': []}
        if 'bids' in obj and 'asks' in obj and obj['type'] == 'ORDER_BOOK':
            sides = ['asks', 'bids']
            for side in sides:
                for offer in obj[side]:
                    order_book[side].append([offer['price'], offer['quantity']])
            order_book['time'] = int(time.time() * 1e3)
            return order_book        
        return {}
