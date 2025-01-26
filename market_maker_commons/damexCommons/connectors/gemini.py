import json
import time
import logging
from ccxt.base.exchange import Exchange as CCXTExchange
from damexCommons.connectors.ccxt import CCXTCommons
from damexCommons.connectors.base import ExchangeWSSCommons

class GeminiCommons(CCXTCommons, ExchangeWSSCommons):
    
    def __init__(self, exchange_connector: CCXTExchange, base_asset: str, quote_asset: str):
        CCXTCommons.__init__(
            self, 
            exchange_connector=exchange_connector, 
            exchange='gemini',
            base_asset=base_asset, 
            quote_asset=quote_asset
        )
        ExchangeWSSCommons.__init__(
            self, 
            wss_url='wss://api.gemini.com/v1/marketdata', 
            exchange='gemini', 
            wss_object_params={
                'order_book': {
                    'url_suffix': '/%s?bids=true&offers=true&trades=false' % (base_asset.upper() + quote_asset.upper()),
                    'request': None,
                    'message_function': self.message_function_order_book
                },
                'trade': {
                    'url_suffix': '/%s?bids=false&offers=false&trades=true' % (base_asset.upper() + quote_asset.upper()),
                    'request': None,
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
        if 'events' in obj:
            for event in obj['events']:
                if event['type'] != 'change':
                    continue
                if event['reason'] in ['initial', 'place']:
                    self.order_book[event['side'] + 's'].append([str(event['price']), str(event['remaining'])]) 
                elif event['reason'] == 'cancel':
                    self.order_book['asks'] = [item for item in self.order_book['asks'] if float(event['price']) != float(item[0])]
            if len(self.order_book['bids']) > 0:
                self.order_book['bids'].sort(key=lambda order: float(order[0]), reverse=True)
                self.order_book['bids'] = self.order_book['bids'][:20]
            if len(self.order_book['asks']) > 0:
                self.order_book['asks'].sort(key=lambda order: float(order[0]))
                self.order_book['asks'] = self.order_book['asks'][:20]
            self.order_book['time'] = int(time.time() * 1e3)
            return self.order_book        
        return {}
                   
    async def message_function_trade(self, msg: str) -> dict:
        obj = json.loads(msg)     
        data = {}
        if 'events' in obj:
            for event in obj['events']:
                if event['type'] != 'trade':
                    continue
                data['time'] = int(time.time() * 1e3)
                data['price'] = float(event['price'])
                data['amount'] = float(event['amount'])
                data['currency'] = self.base_asset
                data['side'] = 'SELL' if event['makerSide'] == 'bid' else 'BUY'
                data['exchange'] = self.exchange        
            #    price = data['price']
            #    amount = data['amount']
            #    time.sleep(5)
            #    match_to = await match_trade_order(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, price=price, amount=amount, trade_side=data['side'].upper())
            #    data.update(match_to)
                return data
        return data