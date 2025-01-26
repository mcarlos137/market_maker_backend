from ccxt.base.exchange import Exchange as CCXTExchange
import logging
import zlib
import json
import time
from damexCommons.connectors.base import ExchangeWSSCommons
from damexCommons.connectors.ccxt import CCXTCommons
from damexCommons.tools.exchange import match_trade_order


class BitmartCommons(CCXTCommons, ExchangeWSSCommons):
    
    def __init__(self, exchange_connector: CCXTExchange, base_asset: str, quote_asset: str):
        CCXTCommons.__init__(
            self, 
            exchange_connector=exchange_connector, 
            exchange='bitmart',
            base_asset=base_asset, 
            quote_asset=quote_asset
        )
        ExchangeWSSCommons.__init__(
            self, 
            wss_url='wss://ws-manager-compress.bitmart.com/api?protocol=1.1', 
            exchange='bitmart', 
            wss_object_params={
                'order_book': {
                    'request': '{"op": "subscribe", "args": ["spot/depth%s:%s_%s"]}' % (20, base_asset, quote_asset),
                    'message_function': self.message_function_order_book
                },
                'ticker': {
                    'request': '{"op": "subscribe", "args": ["spot/ticker:%s_%s"]}' % (base_asset, quote_asset),
                    'message_function': self.message_function_ticker
                },
                'trade': {
                    'request': '{"op": "subscribe", "args": ["spot/trade:%s_%s"]}' % (base_asset, quote_asset),
                    'message_function': self.message_function_trade
                }
            },
            order_book_levels=20
        )
        
    async def fetch_balance(self) -> dict:
        try:
            balance_response = self.exchange_connector.fetch_balance()
            balance = {}
            for b in balance_response['info']['data']['wallet']:
                if not len([i for i in self.exchange_active_markets if b['id'] in i]) > 0:
                    continue
                balance[b['id']] = {'available': b['available'], 'total': b['total']}
            if self.base_asset not in balance:
                balance[self.base_asset] = {'available': 0, 'total':0}
            if self.quote_asset not in balance:
                balance[self.quote_asset] = {'available': 0, 'total':0}
            logging.info('balance %s', balance)
            return balance
        except Exception as e:
            raise e
                                    
    async def message_function_order_book(self, msg: str) -> dict:
        obj = json.loads(inflate(msg))
        if 'data' not in obj:
            return {}
        incoming_data = obj['data'][0]
        if incoming_data.get('asks') is not None and incoming_data.get('bids') is not None:
            order_book_time = int(time.time() * 1000)
            return {
                'time': order_book_time,
                'asks': incoming_data['asks'],
                'bids': incoming_data['bids'],
            }
        return {}
    
    async def message_function_ticker(self, msg: str) -> dict:
        obj = json.loads(inflate(msg))
        if 'data' not in obj:
            return {}
        incoming_data = obj['data'][0]
        if incoming_data.get('last_price') is not None:
            ticker_time = int(time.time() * 1000)
            return {
                'time': ticker_time,
                'lastPrice': float(incoming_data['last_price']),
                'volume': float(incoming_data['quote_volume_24h']),
                'high': float(incoming_data['high_24h']),
                'low': float(incoming_data['low_24h']),
            }
        return {}
    
    async def message_function_trade(self, msg: str) -> dict:
        obj = json.loads(inflate(msg))
        data = {}
        if 'data' in obj:
            incoming_data = obj['data'][0]
            data['time'] = int(incoming_data['s_t'] * 1e3)
            data['price'] = float(incoming_data['price'])
            data['amount'] = float(incoming_data['size'])
            data['currency'] = self.base_asset
            data['side'] = incoming_data['side']
            data['exchange'] = self.exchange
            price = data['price']
            amount = data['amount']
            time.sleep(5)
            match_to = await match_trade_order(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, price=price, amount=amount, trade_side=data['side'].upper())
            data.update(match_to)
            return data
        return data

def inflate(data):
    try:
        decompress = zlib.decompressobj(-zlib.MAX_WBITS)
        inflated = decompress.decompress(data)
        inflated += decompress.flush()
        return inflated.decode('UTF-8')
    except Exception as ex:
        return data