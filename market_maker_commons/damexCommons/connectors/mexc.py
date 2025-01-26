import json
import time
import logging
from ccxt.base.exchange import Exchange as CCXTExchange
from damexCommons.connectors.base import ExchangeWSSCommons
from damexCommons.connectors.ccxt import CCXTCommons
from damexCommons.tools.exchange import match_trade_order

class MexcCommons(CCXTCommons, ExchangeWSSCommons):
    
    def __init__(self, exchange_connector: CCXTExchange, base_asset: str, quote_asset: str):
        CCXTCommons.__init__(
            self, 
            exchange_connector=exchange_connector, 
            exchange='mexc',
            base_asset=base_asset, 
            quote_asset=quote_asset
        )
        ExchangeWSSCommons.__init__(
            self, 
            wss_url='wss://wbs.mexc.com/ws', 
            exchange='mexc', 
            wss_object_params={
                'order_book': {
                    'request': '{"method": "SUBSCRIPTION", "params": ["spot@public.limit.depth.v3.api@%s@%s"]}' % (base_asset + quote_asset, 20),
                    'message_function': self.message_function_order_book
                },
                'ticker': {
                    'request': '{"method": "SUBSCRIPTION", "params": ["spot@public.kline.v3.api@%s@Day1"]}' % (base_asset + quote_asset),
                    'message_function': self.message_function_ticker
                },
                'trade': {
                    'request': '{"method": "SUBSCRIPTION", "params": ["spot@public.deals.v3.api@%s"]}' % (base_asset + quote_asset),
                    'message_function': self.message_function_trade
                }
            },
            order_book_levels=20
        )
    
    async def fetch_balance(self) -> dict:
        try:
            balance_response = self.exchange_connector.fetch_balance()
            balance = {}
            for b in balance_response['info']['balances']:
                if not len([i for i in self.exchange_active_markets if b['asset'] in i]) > 0:
                    continue
                balance[b['asset']] = {'available': float(b['free']), 'total': float(b['free']) + float(b['locked'])}
            logging.info('balance %s', balance)
            return balance
        except Exception as e:
            raise e
                                
    async def message_function_order_book(self, msg: str) -> dict:
        obj = json.loads(msg)
        if obj.get('c') is None:
            return {}
        if obj['c'] == 'spot@public.limit.depth.v3.api@%s@%s' % (self.base_asset + self.quote_asset, self.order_book_levels):
            values = obj['d']
            order_book_time = int(time.time() * 1000)
            return {
                'time': order_book_time,
                'asks': list(map(lambda l: [l['p'], l['v']], values['asks'])),
                'bids': list(map(lambda l: [l['p'], l['v']], values['bids'])),
            }
        return {}
    
    async def message_function_ticker(self, msg: str) -> dict:
        obj = json.loads(msg)
        if obj.get('c') is None:
            return {}
        if obj['c'] == 'spot@public.kline.v3.api@%s@Day1' % (self.base_asset + self.quote_asset):
            values = obj['d']['k']
            ticker_time = int(time.time() * 1000)
            return {
                'time': ticker_time,
                'lastPrice': float(values['c']),
                'volume': float(values['a']),
                'high': float(values['h']),
                'low': float(values['l']),
            }
        return {}
    
    async def message_function_trade(self, msg: str) -> dict:
        obj = json.loads(msg)
        if obj.get('c') is None:
            return {}
        if obj['c'] == 'spot@public.deals.v3.api@%s' % (self.base_asset + self.quote_asset):
            data = {}
            values = obj['d']['deals'][0]
            data['time'] = values['t']
            data['price'] = float(values['p'])
            data['amount'] = float(values['v'])
            data['currency'] = self.base_asset
            data['side'] = 'sell' if values['S'] == 2 else 'buy'
            data['exchange'] = self.exchange
            price = data['price']
            amount = data['amount']
            time.sleep(5)
            match_to = await match_trade_order(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, price=price, amount=amount, trade_side=data['side'].upper())
            data.update(match_to)
            return data
        return {}