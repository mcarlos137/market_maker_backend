from ccxt.base.exchange import Exchange as CCXTExchange
import logging
import time
import gzip
import random
import json
from damexCommons.connectors.base import ExchangeWSSCommons
from damexCommons.connectors.ccxt import CCXTCommons
from damexCommons.tools.exchange import match_trade_order

class CoinexCommons(CCXTCommons, ExchangeWSSCommons):
    
    def __init__(self, exchange_connector: CCXTExchange, base_asset: str, quote_asset: str):
        CCXTCommons.__init__(
            self, 
            exchange_connector=exchange_connector, 
            exchange='coinex',
            base_asset=base_asset, 
            quote_asset=quote_asset
        )        
        ExchangeWSSCommons.__init__(
            self, 
            wss_url='wss://socket.coinex.com/v2/spot', 
            exchange='coinex', 
            wss_object_params={
                'order_book': {
                    'request': '{"method": "depth.subscribe", "params": {"market_list": [["%s", %s, "0", true]]}, "id": %s}' % (base_asset + quote_asset, 20, random.randint(100000, 130000)),
                    'message_function': self.message_function_order_book
                },
                'ticker': {
                    'request': '{"method": "state.subscribe", "params": {"market_list": [["%s"]]}, "id": %s}' % (base_asset + quote_asset, random.randint(100000, 130000)),
                    'message_function': self.message_function_ticker
                },
                'trade': {
                    'request': '{"method": "deals.subscribe", "params": {"market_list": [["%s"]]}, "id": %s}' % (base_asset + quote_asset, random.randint(100000, 130000)),
                    'message_function': self.message_function_trade
                },
            },
            order_book_levels=20
        )
        
    async def fetch_balance(self) -> dict:
       raise NotImplementedError
    
    async def message_function_order_book(self, msg: str) -> dict:
        obj = json.loads(gzip.decompress(msg))
        if 'method' in obj and obj['method'] == 'depth.update' and 'data' in obj:
            return {
                'time': int(obj['data']['depth']['updated_at']),
                'asks': obj['data']['depth']['asks'],
                'bids': obj['data']['depth']['bids'],
            }        
        return {}

    async def message_function_ticker(self, msg: str) -> dict:
        obj = json.loads(gzip.decompress(msg))
        if 'method' in obj and obj['method'] == 'state.update' and 'data' in obj:
            ticker_time = int(time.time() * 1000)
            return {
                'time': ticker_time,
                'lastPrice': float(obj['data']['state_list'][0]['last']),
                'volume': float(obj['data']['state_list'][0]['value']),
                'high': float(obj['data']['state_list'][0]['high']),
                'low': float(obj['data']['state_list'][0]['low']),
            }
        return {}
    
    async def message_function_trade(self, msg: str) -> dict:
        obj = json.loads(gzip.decompress(msg))
        data = {}
        if 'method' in obj and obj['method'] == 'deals.update' and 'data' in obj:
            for trade in obj['data']['deal_list']:
                data['time'] = int(trade['created_at'])
                data['price'] = float(trade['price'])
                data['amount'] = float(trade['amount'])
                data['currency'] = self.base_asset
                data['side'] = str(trade['side']).upper()
                data['exchange'] = self.exchange                
            #    price = data['price']
            #    amount = data['amount']
            #    time.sleep(5)
            #    match_to = await match_trade_order(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, price=price, amount=amount, trade_side=data['side'].upper())
            #    data.update(match_to)
                return data
        return data