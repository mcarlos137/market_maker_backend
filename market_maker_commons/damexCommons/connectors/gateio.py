import json
import time
import logging
from ccxt.base.exchange import Exchange as CCXTExchange
from damexCommons.connectors.ccxt import CCXTCommons
from damexCommons.connectors.base import ExchangeWSSCommons

class GateioCommons(CCXTCommons, ExchangeWSSCommons):
    
    def __init__(self, exchange_connector: CCXTExchange, base_asset: str, quote_asset: str):
        CCXTCommons.__init__(
            self, 
            exchange_connector=exchange_connector, 
            exchange='gateio',
            base_asset=base_asset, 
            quote_asset=quote_asset
        )
        ExchangeWSSCommons.__init__(
            self, 
            wss_url='wss://api.gateio.ws/ws/v4/', 
            exchange='gateio', 
            wss_object_params={
                'order_book': {
                    'request': '{"time": %s, "channel": "spot.order_book", "event":"subscribe", "payload": ["%s", "%s", "100ms"]}' % (int(time.time()), base_asset.upper() + '_' + quote_asset.upper(), 20),
                    'message_function': self.message_function_order_book
                },
                'ticker': {
                    'request': '{"time": %s, "channel": "spot.tickers", "event":"subscribe", "payload": ["%s"]}' % (int(time.time()), base_asset.upper() + '_' + quote_asset.upper()),
                    'message_function': self.message_function_ticker
                },
                'trade': {
                    'request': '{"time": %s, "channel": "spot.trades", "event":"subscribe", "payload": ["%s"]}' % (int(time.time()), base_asset.upper() + '_' + quote_asset.upper()),
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
        if obj['channel'] == 'spot.order_book' and 'result' in obj and 't' in obj['result']:
            return {
                'time': int(obj['result']['t']),
                'asks': obj['result']['asks'],
                'bids': obj['result']['bids'],
            }        
        return {}
    
    async def message_function_ticker(self, msg: str) -> dict:
        obj = json.loads(msg)
        if obj['channel'] == 'spot.tickers' and 'result' in obj and 'currency_pair' in obj['result']:
            return {
                'time': int(obj['time_ms']),
                'lastPrice': float(obj['result']['last']),
                'volume': float(obj['result']['quote_volume']),
                'high': float(obj['result']['high_24h']),
                'low': float(obj['result']['low_24h']),
            }
        return {}
        
    async def message_function_trade(self, msg: str) -> dict:
        obj = json.loads(msg)
        data = {}
        if obj['channel'] == 'spot.trades' and 'result' in obj and 'id' in obj['result']:
            data['time'] = int(obj['result']['create_time_ms'].split('.')[0])
            data['price'] = float(obj['result']['price'])
            data['amount'] = float(obj['result']['amount'])
            data['currency'] = self.base_asset
            data['side'] = str(obj['result']['side']).upper()
            data['exchange'] = self.exchange
        #    price = data['price']
        #    amount = data['amount']
        #    time.sleep(5)
        #    match_to = await match_trade_order(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, price=price, amount=amount, trade_side=data['side'].upper())
        #    data.update(match_to)
            return data
        return data