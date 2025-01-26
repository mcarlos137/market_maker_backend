import json
from ccxt.base.exchange import Exchange as CCXTExchange
from damexCommons.connectors.base import ExchangeWSSCommons
from damexCommons.connectors.ccxt import CCXTCommons

class BitstampCommons(CCXTCommons, ExchangeWSSCommons):
    
    def __init__(self, exchange_connector: CCXTExchange, base_asset: str, quote_asset: str):
        CCXTCommons.__init__(
            self, 
            exchange_connector=exchange_connector, 
            exchange='bitstamp',
            base_asset=base_asset, 
            quote_asset=quote_asset
        )
        
        ExchangeWSSCommons.__init__(
            self, 
            wss_url='wss://ws.bitstamp.net', 
            exchange='bitstamp', 
            wss_object_params={
                'order_book': {
                    'request': '{"event": "bts:subscribe", "data": {"channel": "order_book_%s"}}' % (base_asset.lower() + quote_asset.lower()),
                    'message_function': self.message_function_order_book
                },
                #'ticker': {
                #    'request': '{"event": "bts:subscribe", "data": {"channel": "order_book_%s"}}' % (base_asset.lower() + quote_asset.lower()),
                #    'message_function': self.message_function_ticker
                #},
                'trade': {
                    'request': '{"event": "bts:subscribe", "data": {"channel": "live_trades_%s"}}' % (base_asset.lower() + quote_asset.lower()),
                    'message_function': self.message_function_trade
                }
            },
            order_book_levels=20
        )
        
    async def fetch_balance(self) -> dict:
        raise NotImplementedError
    
    async def message_function_order_book(self, msg: str) -> dict:
        obj = json.loads(msg)
        if 'data' in obj and obj['event'] == 'data':
            return {
                'time': int(obj['data']['timestamp']) * 1e3,
                'asks': obj['data']['asks'][:20],
                'bids': obj['data']['bids'][:20],
            }        
        return {}
    
    async def message_function_ticker(self, msg: str) -> dict:
        obj = json.loads(msg)
        if 'data' in obj and obj['event'] == 'data':
            print('obj2', obj)
        #if obj['channel'] == 'spot.tickers' and 'result' in obj and 'currency_pair' in obj['result']:
        #    return {
        #        'time': int(obj['time_ms']),
        #        'lastPrice': float(obj['result']['last']),
        #        'volume': float(obj['result']['quote_volume']),
        #        'high': float(obj['result']['high_24h']),
        #        'low': float(obj['result']['low_24h']),
        #    }
        return {}
        
    async def message_function_trade(self, msg: str) -> dict:
        obj = json.loads(msg)
        if 'data' in obj and obj['event'] == 'data':
            print('obj3', obj)
        data = {}
        #if obj['channel'] == 'spot.trades' and 'result' in obj and 'id' in obj['result']:
        #    data['time'] = int(obj['result']['create_time_ms'].split('.')[0])
        #    data['price'] = float(obj['result']['price'])
        #    data['amount'] = float(obj['result']['amount'])
        #    data['currency'] = self.base_asset
        #    data['side'] = str(obj['result']['side']).upper()
        #    data['exchange'] = self.exchange
        #    price = data['price']
        #    amount = data['amount']
        #    time.sleep(5)
        #    match_to = await match_trade_order(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, price=price, amount=amount, trade_side=data['side'].upper())
        #    data.update(match_to)
        #    return data
        return data