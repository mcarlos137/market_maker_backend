import json
import time
import logging
import binascii
from ccxt.base.exchange import Exchange as CCXTExchange
from damexCommons.connectors.ccxt import CCXTCommons
from damexCommons.connectors.base import ExchangeWSSCommons

class KrakenCommons(CCXTCommons, ExchangeWSSCommons):
    
    def __init__(self, exchange_connector: CCXTExchange, base_asset: str, quote_asset: str):
        CCXTCommons.__init__(
            self, 
            exchange_connector=exchange_connector, 
            exchange='kraken',
            base_asset=base_asset, 
            quote_asset=quote_asset
        )
        ExchangeWSSCommons.__init__(
            self, 
            wss_url='wss://ws.kraken.com/v2', 
            exchange='kraken', 
            wss_object_params={
                'order_book': {
                    'request': '{"method": "subscribe", "params": {"channel": "book", "symbol": ["%s/%s"], "depth": 25}}' % (base_asset.upper(), quote_asset.upper()),
                    'message_function': self.message_function_order_book
                },
                'ticker': {
                    'request': '{"method": "subscribe", "params": {"channel": "ticker", "symbol": ["%s/%s"]}}' % (base_asset.upper(), quote_asset.upper()),
                    'message_function': self.message_function_ticker
                },
                'trade': {
                    'request': '{"method": "subscribe", "params": {"channel": "trade", "symbol": ["%s/%s"], "snapshot": false}}' % (base_asset.upper(), quote_asset.upper()),
                    'message_function': self.message_function_trade
                }
            },
            order_book_levels=20
        )
        self.order_book = {'asks': [], 'bids': []}
        self.checksum = None
        
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
        if 'data' in obj and 'channel' in obj and obj['channel'] == 'book':
            values = obj['data'][0]
            print('order_book', values)
            if obj['type'] == 'snapshot':
                self.order_book['asks'] = []
                self.order_book['bids'] = []
                checksum_asks = ''
                for ask in values['asks']: 
                    self.order_book['asks'].append([str(ask['price']), str(ask['qty'])]) 
                    checksum_asks += str(ask['price']).replace('.', '').lstrip('0') + str(ask['qty']).replace('.', '').lstrip('0')
                    #if len(self.order_book['asks']) >= 20:
                    #    break
                checksum_bids = ''
                for bid in values['bids']: 
                    self.order_book['bids'].append([str(bid['price']), str(bid['qty'])]) 
                    checksum_bids += str(bid['price']).replace('.', '').lstrip('0') + str(bid['qty']).replace('.', '').lstrip('0')
                    #if len(self.order_book['bids']) >= 20:
                    #    break
                checksum = checksum_asks + checksum_bids
                print('comparing checksum ------', binascii.crc32(checksum.encode('utf8')), values['checksum'])
                self.checksum = checksum
            elif obj['type'] == 'update':
                for ask in values['asks']:
                    self.order_book['asks'] = [item for item in self.order_book['asks'] if float(ask['price']) != float(item[0])]
                    if float(ask['qty']) != 0:
                        self.order_book['asks'].append([str(ask['price']), str(ask['qty'])]) 
                for bid in values['bids']:
                    self.order_book['bids'] = [item for item in self.order_book['bids'] if float(bid['price']) != float(item[0])]
                    if float(bid['qty']) != 0:
                        self.order_book['bids'].append([str(bid['price']), str(bid['qty'])]) 
                if len(self.order_book['bids']) > 0:
                    self.order_book['bids'].sort(key=lambda order: float(order[0]), reverse=True)
                    self.order_book['bids'] = self.order_book['bids'][:20]
                if len(self.order_book['asks']) > 0:
                    self.order_book['asks'].sort(key=lambda order: float(order[0]))
                    self.order_book['asks'] = self.order_book['asks'][:20]
            self.order_book['time'] = int(time.time() * 1e3)
            return self.order_book        
        return {}
    
    async def message_function_ticker(self, msg: str) -> dict:
        obj = json.loads(msg)
        if 'data' in obj and 'channel' in obj and obj['channel'] == 'trade' and obj['type'] == 'update':
            return {
                'time': int(time.time() * 1e3),
                'lastPrice': float(obj['data'][0]['last']),
                'volume': float(obj['data'][0]['volume']),
                'high': float(obj['data'][0]['high']),
                'low': float(obj['data'][0]['low']),
            }
        return {}
                              
    async def message_function_trade(self, msg: str) -> dict:
        obj = json.loads(msg)
        data = {}
        if 'data' in obj and 'channel' in obj and obj['channel'] == 'trade':
            for trade in obj['data']:
                data['time'] = int(time.time() * 1e3)
                data['price'] = float(trade['price'])
                data['amount'] = float(trade['qty'])
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