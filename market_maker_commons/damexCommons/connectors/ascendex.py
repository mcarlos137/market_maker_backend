import json
import time
import random
import logging
from ccxt.base.exchange import Exchange as CCXTExchange
from damexCommons.connectors.base import ExchangeWSSCommons
from damexCommons.connectors.ccxt import CCXTCommons
from damexCommons.tools.exchange import match_trade_order

class AscendexCommons(CCXTCommons, ExchangeWSSCommons):
    
    def __init__(self, exchange_connector: CCXTExchange, base_asset: str, quote_asset: str):
        CCXTCommons.__init__(
            self, 
            exchange_connector=exchange_connector, 
            exchange='ascendex',
            base_asset=base_asset, 
            quote_asset=quote_asset,
        )
        ExchangeWSSCommons.__init__(
            self, 
            wss_url='wss://ascendex.com/1/api/pro/v1/stream', 
            exchange='ascendex', 
            wss_object_params={
                'order_book': {
                    'request': '{ "op": "sub", "id": "abc%s", "ch":"depth:%s/%s" }' % (random.randint(10000, 13000), base_asset, quote_asset),
                    'message_function': self.message_function_order_book
                },
                'ticker': {
                    'request': '{ "op": "sub", "id": "abc%s", "ch":"bar:1d:%s/%s" }' % (random.randint(10000, 13000), base_asset, quote_asset),
                    'message_function': self.message_function_ticker
                },
                'trade': {
                    'request': '{ "op": "sub", "id": "abc%s", "ch":"trades:%s/%s" }' % (random.randint(10000, 13000), base_asset, quote_asset),
                    'message_function': self.message_function_trade
                }
            },
            order_book_levels=20
        )
        self.order_book = {'asks': [], 'bids': []}
        
    async def fetch_balance(self) -> dict:
        try:
            balance_response = self.exchange_connector.fetch_balance()
            balance = {}
            for b in balance_response['info']['data']:
                if not len([i for i in self.exchange_active_markets if b['asset'] in i]) > 0:
                    continue
                balance[b['asset']] = {'available': float(b['availableBalance']), 'total': float(b['totalBalance'])}
            logging.info('balance %s', balance)
            return balance
        except Exception as e:
            raise e
        
    async def message_function_order_book(self, msg: str) -> dict:
        obj = json.loads(msg)
        if obj['m'] == 'depth':
            values = obj['data'] 
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
            order_book_time = int(time.time() * 1000)
            self.order_book['time'] = order_book_time
            return self.order_book
        elif obj['m'] == 'ping':
            self.wss.send('{ "op": "pong" }')
            return {}   
        return {}

    async def message_function_ticker(self, msg: str) -> dict:
        obj = json.loads(msg)
        if obj['m'] == 'bar':
            ticker_time = int(time.time() * 1000)
            return {
                'time': ticker_time,
                'lastPrice': float(obj['data']['c']),
                'volume': float(obj['data']['v']) * (float(obj['data']['l']) + float(obj['data']['h'])) / 2,
                'high': float(obj['data']['h']),
                'low': float(obj['data']['l']),
            }
        elif obj['m'] == 'ping':
            self.wss.send('{ "op": "pong" }')
            return {}   
        return {}
    
    async def message_function_trade(self, msg: str) -> dict:
        obj = json.loads(msg)
        data = {}        
        if obj['m'] == 'trades' and 'data' in obj:
            trade = obj['data'][0]
            data['time'] = trade['ts']
            data['price'] = float(trade['p'])
            data['amount'] = float(trade['q'])
            data['currency'] = self.base_asset
            data['side'] = 'SELL' if trade['bm'] else 'BUY'
            data['exchange'] = self.exchange
            price = data['price']
            amount = data['amount']
            time.sleep(5)
            match_to = await match_trade_order(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, price=price, amount=amount, trade_side=data['side'].upper())
            data.update(match_to)
            return data
        elif obj['m'] == 'ping':
            self.wss.send('{ "op": "pong" }')
            return {}   
        return data