import json
import time
import logging
from ccxt.base.exchange import Exchange as CCXTExchange
from damexCommons.connectors.ccxt import CCXTCommons
from damexCommons.connectors.base import ExchangeWSSCommons

class BitvavoCommons(CCXTCommons, ExchangeWSSCommons):
    
    def __init__(self, exchange_connector: CCXTExchange, base_asset: str, quote_asset: str):
        CCXTCommons.__init__(
            self, 
            exchange_connector=exchange_connector, 
            exchange='bitvavo',
            base_asset=base_asset, 
            quote_asset=quote_asset
        )    
        ExchangeWSSCommons.__init__(
            self, 
            wss_url='wss://ws.bitvavo.com/v2/', 
            exchange='bitvavo', 
            wss_object_params={
                'order_book': {
                    'request': '{"action": "subscribe", "channels": [{"name": "book", "markets": ["%s-%s"]}]}' % (base_asset.upper(), quote_asset.upper()),
                    'message_function': self.message_function_order_book
                },
                'ticker': {
                    'request': '{"action": "subscribe", "channels": [{"name": "ticker24h", "markets": ["%s-%s"]}]}' % (base_asset.upper(), quote_asset.upper()),
                    'message_function': self.message_function_ticker
                },
                'trade': {
                    'request': '{"action": "subscribe", "channels": [{"name": "trades", "markets": ["%s-%s"]}]}' % (base_asset.upper(), quote_asset.upper()) ,
                    'message_function': self.message_function_trade
                }
            },
            order_book_levels=20
        )
        self.order_book = {'asks': [], 'bids': []}
        
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
        if 'bids' in obj and 'asks' in obj:
            for ask in obj['asks']:
                self.order_book['asks'] = [item for item in self.order_book['asks'] if float(ask[0]) != float(item[0])]
                if float(ask[1]) != 0:
                    self.order_book['asks'].append(ask) 
            for bid in obj['bids']:
                self.order_book['bids'] = [item for item in self.order_book['bids'] if float(bid[0]) != float(item[0])]
                if float(bid[1]) != 0:
                    self.order_book['bids'].append(bid) 
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
        if 'event' in obj and obj['event'] == 'ticker24h' and 'data' in obj:
            return {
                'time': int(obj['data']['timestamp']),
                'lastPrice': float(obj['data']['last']),
                'volume': float(obj['data']['volumeQuote']),
                'high': float(obj['data']['high']),
                'low': float(obj['data']['low']),
            }
        return {}
     
    {
  "event": "trade",
  "timestamp": 1566817150381,
  "market": "BTC-EUR",
  "id": "391f4d94-485f-4fb0-b11f-39da1cfcfc2d",
  "amount": "0.00096361",
  "price": "9311.2",
  "side": "sell"
} 
            
    async def message_function_trade(self, msg: str) -> dict:
        obj = json.loads(msg)
        data = {}
        if 'event' in obj and obj['event'] == 'trade':
            data['time'] = int(obj['timestamp'])
            data['price'] = float(obj['price'])
            data['amount'] = float(obj['amount'])
            data['currency'] = self.base_asset
            data['side'] = str(obj['side']).upper()
            data['exchange'] = self.exchange
        #    price = data['price']
        #    amount = data['amount']
        #    time.sleep(5)
        #    match_to = await match_trade_order(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, price=price, amount=amount, trade_side=data['side'].upper())
        #    data.update(match_to)
            return data
        return data
