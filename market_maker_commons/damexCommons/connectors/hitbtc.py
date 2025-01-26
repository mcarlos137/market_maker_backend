import json
import random
import logging
from ccxt.base.exchange import Exchange as CCXTExchange
from damexCommons.connectors.ccxt import CCXTCommons
from damexCommons.connectors.base import ExchangeWSSCommons

class HitbtcCommons(CCXTCommons, ExchangeWSSCommons):
    
    def __init__(self, exchange_connector: CCXTExchange, base_asset: str, quote_asset: str):
        CCXTCommons.__init__(
            self, 
            exchange_connector=exchange_connector, 
            exchange='hitbtc',
            base_asset=base_asset, 
            quote_asset=quote_asset
        )
        ExchangeWSSCommons.__init__(
            self, 
            wss_url='wss://api.hitbtc.com/api/3/ws/public', 
            exchange='hitbtc', 
            wss_object_params={
                'order_book': {
                    'request': '{"method": "subscribe", "ch": "orderbook/D20/100ms", "params":{"symbols": ["%s"]}, "id": "%s"}' % (base_asset.upper() + quote_asset.upper(), random.randint(1000, 1300)),
                    'message_function': self.message_function_order_book
                },
                'ticker': {
                    'request': '{"method": "subscribe", "ch": "ticker/price/1s/batch", "params":{"symbols": ["%s"]}, "id": "%s"}' % (base_asset.upper() + quote_asset.upper(), random.randint(1000, 1300)),
                    'message_function': self.message_function_ticker
                },
                'trade': {
                    'request': '{"method": "subscribe", "ch": "trades", "params":{"symbols": ["%s"]}, "id": "%s"}' % (base_asset.upper() + quote_asset.upper(), random.randint(1000, 1300)),
                    'message_function': self.message_function_trade
                }
            },
            order_book_levels=20
        )
        
    async def fetch_balance(self) -> dict:
        try:
            balance_response = self.exchange_connector.fetch_balance()
            logging.info('balance %s', balance_response)
            #balance = {}
            #for b in balance_response:
            #    if b not in ['info', 'free', 'used', 'total']:
            #        balance[b] = {'available': float(balance_response[b]['free']), 'total': float(balance_response[b]['total'])}
            #logging.info(f'balance {balance}')
            #return balance
        except Exception as e:
            raise e
    
    
    async def message_function_order_book(self, msg: str) -> dict:
        obj = json.loads(msg)     
        if 'ch' in obj and obj['ch'] == 'orderbook/D20/100ms' and 'data' in obj:
            return {
                'time': int(obj['data'][self.base_asset + self.quote_asset]['t']),
                'asks': obj['data'][self.base_asset + self.quote_asset]['a'],
                'bids': obj['data'][self.base_asset + self.quote_asset]['b'],
            }        
        return {}
    
    async def message_function_ticker(self, msg: str) -> dict:
        obj = json.loads(msg)
        if 'ch' in obj and obj['ch'] == 'ticker/price/1s/batch' and 'data' in obj:
            return {
                'time': int(obj['data'][self.base_asset + self.quote_asset]['t']),
                'lastPrice': float(obj['data'][self.base_asset + self.quote_asset]['c']),
                'volume': float(obj['data'][self.base_asset + self.quote_asset]['q']),
                'high': float(obj['data'][self.base_asset + self.quote_asset]['h']),
                'low': float(obj['data'][self.base_asset + self.quote_asset]['l']),
            }
        return {}
                
    async def message_function_trade(self, msg: str) -> dict:
        obj = json.loads(msg)
        data = {}
        if 'ch' in obj and obj['ch'] == 'trades' and 'update' in obj:
            for trade in obj['update'][self.base_asset + self.quote_asset]:
                data['time'] = int(trade['t'])
                data['price'] = float(trade['p'])
                data['amount'] = float(trade['q'])
                data['currency'] = self.base_asset
                data['side'] = str(trade['s']).upper()
                data['exchange'] = self.exchange
            #    price = data['price']
            #    amount = data['amount']
            #    time.sleep(5)
            #    match_to = await match_trade_order(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, price=price, amount=amount, trade_side=data['side'].upper())
            #    data.update(match_to)
                return data
        return data