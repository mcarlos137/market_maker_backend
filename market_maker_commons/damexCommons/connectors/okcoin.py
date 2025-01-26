from ccxt.base.exchange import Exchange as CCXTExchange
import logging
import time
import gzip
import random
import json
from damexCommons.connectors.base import ExchangeWSSCommons
from damexCommons.connectors.ccxt import CCXTCommons
from damexCommons.tools.exchange import match_trade_order

class OkcoinCommons(CCXTCommons, ExchangeWSSCommons):
    
    def __init__(self, exchange_connector: CCXTExchange, base_asset: str, quote_asset: str):
        CCXTCommons.__init__(
            self, 
            exchange_connector=exchange_connector, 
            exchange='okcoin',
            base_asset=base_asset, 
            quote_asset=quote_asset
        )
        ExchangeWSSCommons.__init__(
            self, 
            wss_url='wss://real.okcoin.com:8443/ws/v5/public', 
            exchange='okcoin',             
            wss_object_params={
                'order_book': {
                    'request': '{"op": "subscribe", "args": [{"channel": "books", "instId": "%s-%s"}]}' % (base_asset, quote_asset),
                    'message_function': self.message_function_order_book
                },
                'ticker': {
                    'request': '{"op": "subscribe", "args": [{"channel": "tickers", "instId": "%s-%s"}]}' % (base_asset, quote_asset),
                    'message_function': self.message_function_ticker
                },
                'trade': {
                    'request': '{"op": "subscribe", "args": [{"channel": "trades", "instId": "%s-%s"}]}' % (base_asset, quote_asset),
                    'message_function': self.message_function_trade
                },
            },
            order_book_levels=20
        )
        self.order_book = {'asks': [], 'bids': []}
        
    async def fetch_balance(self) -> dict:
       raise NotImplementedError
    
    async def message_function_order_book(self, msg: str) -> dict:
        obj = json.loads(msg)
        if 'data' in obj:
            values = obj['data'][0]
            if obj['action'] == 'snapshot':
                self.order_book['asks'] = values['asks'][:20]
                self.order_book['bids'] = values['bids'][:20]
            elif obj['action'] == 'update':
                for ask in values['asks']:
                    self.order_book['asks'] = [item for item in self.order_book['asks'] if float(ask[0]) != float(item[0])]
                    if float(ask[1]) != 0:
                        self.order_book['asks'].append(ask) 
                for bid in values['bids']:
                    self.order_book['bids'] = [item for item in self.order_book['bids'] if float(bid[0]) != float(item[0])]
                    if float(bid[1]) != 0:
                        self.order_book['bids'].append(bid) 
                if len(self.order_book['bids']) > 0:
                    self.order_book['bids'].sort(key=lambda order: float(order[0]), reverse=True)
                    self.order_book['bids'] = self.order_book['bids'][:20]
                if len(self.order_book['asks']) > 0:
                    self.order_book['asks'].sort(key=lambda order: float(order[0]))
                    self.order_book['asks'] = self.order_book['asks'][:20]
            self.order_book['time'] = int(values['ts'])
            return self.order_book
        return {}

    async def message_function_ticker(self, msg: str) -> dict:
        obj = json.loads(msg)
        if 'data' in obj:
            values = obj['data'][0]
            ticker_time = int(values['ts'])            
            return {
                'time': ticker_time,
                'lastPrice': float(values['last']),
                'volume': float(values['volCcy24h']),
                'high': float(values['high24h']),
                'low': float(values['low24h']),
            }
        return {}
    
    async def message_function_trade(self, msg: str) -> dict:
        obj = json.loads(msg)
        data = {}
        if 'data' in obj:
            for trade in obj['data']:
                data['time'] = int(trade['ts'])
                data['price'] = float(trade['px'])
                data['amount'] = float(trade['sz'])
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