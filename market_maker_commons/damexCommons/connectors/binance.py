import time
import json
import logging
import random
from ccxt.base.exchange import Exchange as CCXTExchange
from damexCommons.connectors.base import ExchangeWSSCommons
from damexCommons.connectors.ccxt import CCXTCommons
from damexCommons.tools.exchange import match_trade_order


class BinanceCommons(CCXTCommons, ExchangeWSSCommons):
    
    def __init__(self, exchange_connector: CCXTExchange, base_asset: str, quote_asset: str):
        CCXTCommons.__init__(
            self, 
            exchange_connector=exchange_connector, 
            exchange='binance',
            base_asset=base_asset, 
            quote_asset=quote_asset
        )
        ExchangeWSSCommons.__init__(
            self, 
            wss_url='wss://stream.binance.com:443/ws', 
            exchange='binance', 
            wss_object_params={
                'order_book': {
                    'request': '{"method":"SUBSCRIBE", "params": ["%s@depth%s"], "id": %s}' % (base_asset.lower() + quote_asset.lower(), 20, random.randint(10000000, 13000000)),
                    'message_function': self.message_function_order_book
                },
                'ticker': {
                    'request': '{"method":"SUBSCRIBE", "params": ["%s@ticker"], "id": %s}' % (base_asset.lower() + quote_asset.lower(), random.randint(10000000, 13000000)),
                    'message_function': self.message_function_ticker
                },
                'trade': {
                    'request': '{"method":"SUBSCRIBE", "params": ["%s@trade"], "id": %s}' % (base_asset.lower() + quote_asset.lower(), random.randint(10000000, 13000000)),
                    'message_function': self.message_function_trade
                }
            },
            order_book_levels=20
        )
        
    async def fetch_balance(self) -> dict:
        try:
            balance_response = self.exchange_connector.fetch_balance()
            balance = {}
            #
            for asset in balance_response:
                if not len([i for i in self.exchange_active_markets if asset in i]) > 0:
                    continue
                balance[asset] = {'available': float(balance_response[asset]['free']), 'total': float(balance_response[asset]['total'])}
            logging.info('balance %s', balance)
            return balance
        except Exception as e:
            raise e
                
    async def message_function_order_book(self, msg: str) -> dict:
        obj = json.loads(msg)
        if 'lastUpdateId' in obj:
            order_book_time = int(time.time() * 1000)
            return {
                'time': order_book_time,
                'asks': obj['asks'],
                'bids': obj['bids'],
            }        
        return {}
    
    async def message_function_ticker(self, msg: str) -> dict:
        obj = json.loads(msg)
        if not u'result' in obj:
            ticker_time = int(obj['E'])
            return {
                'time': ticker_time,
                'lastPrice': float(obj['c']),
                'volume': float(obj['q']),
                'high': float(obj['h']),
                'low': float(obj['l']),
            }
        return {}
    
    
    async def message_function_trade(self, msg: str) -> dict:
        obj = json.loads(msg)
        data = {}
        if u'e' in obj and obj['e'] == 'trade':
            data['time'] = obj['E']
            data['price'] = float(obj['p'])
            data['amount'] = float(obj['q'])
            data['currency'] = self.base_asset
            data['side'] = 'SELL' if obj['m'] else 'BUY'
            data['exchange'] = self.exchange
            price = data['price']
            amount = data['amount']
            time.sleep(5)
            match_to = await match_trade_order(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, price=price, amount=amount, trade_side=data['side'].upper())
            data.update(match_to)
            return data
        return data