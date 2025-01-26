import random
import json
import logging
import requests
import time
from ccxt.base.exchange import Exchange as CCXTExchange
from damexCommons.connectors.base import ExchangeWSSCommons
from damexCommons.connectors.ccxt import CCXTCommons

class KucoinCommons(CCXTCommons, ExchangeWSSCommons):
    
    def __init__(self, exchange_connector: CCXTExchange, base_asset: str, quote_asset: str):
        CCXTCommons.__init__(
            self, 
            exchange_connector=exchange_connector, 
            exchange='kucoin',
            base_asset=base_asset, 
            quote_asset=quote_asset
        )
        response = requests.post('https://api.kucoin.com' + '/api/v1/bullet-public', timeout=7)
        token = response.json()['data']['token']        
        ExchangeWSSCommons.__init__(
            self, 
            wss_url='wss://ws-api-spot.kucoin.com/?token=%s&[connectId=%s]' % (token, random.randint(100000, 130000)), 
            exchange='kucoin', 
            wss_object_params={
                'ping': '{"id": "%s","type": "ping"}' % (random.randint(1000000, 1300000)),
                'order_book': {
                    'request': '{"id": %s, "type": "subscribe", "topic": "/spotMarket/level2Depth50:%s-%s", "response": true}' % (random.randint(1000000, 1300000), base_asset, quote_asset),
                    'message_function': self.message_function_order_book
                },
                'ticker': {
                    'request': '{"id": %s, "type": "subscribe", "topic": "/market/snapshot:%s-%s", "response": true}' % (random.randint(1000000, 1300000), base_asset, quote_asset),
                    'message_function': self.message_function_ticker
                },
                'trade': {
                    'request': '{"id": %s, "type": "subscribe", "topic": "/market/match:%s-%s", "response": true}' % (random.randint(1000000, 1300000), base_asset, quote_asset),
                    'message_function': self.message_function_trade
                }
            },
            order_book_levels=20
        )
        self.order_book = None
        
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
        if obj['type'] != 'message':
            return {}
        if self.order_book is None or self.order_book != obj['data']:
            self.order_book = obj['data']
        else:
            return {}
        return self.order_book

    async def message_function_ticker(self, msg: str) -> dict:
        obj = json.loads(msg)
        if obj['type'] != 'message':
            return {}
        ticker_time = int(time.time() * 1000)
        return {
            'time': ticker_time,
            'lastPrice': float(obj['data']['data']['lastTradedPrice']),
            'volume': float(obj['data']['data']['marketChange24h']['volValue']),
            'high': float(obj['data']['data']['marketChange24h']['high']),
            'low': float(obj['data']['data']['marketChange24h']['low']),
        }
        
    async def message_function_trade(self, msg: str) -> dict:
        obj = json.loads(msg)
        if obj['type'] != 'message':
            return {}
        trade = obj['data']
        data = {}
        data['time'] = int(trade['time'].replace('000000', ''))
        data['price'] = float(trade['price'])
        data['amount'] = float(trade['size'])
        data['currency'] = self.base_asset
        data['side'] = str(trade['side']).upper()
        data['exchange'] = self.exchange
    #    price = data['price']
    #    amount = data['amount']
    #    time.sleep(5)
    #    match_to = await match_trade_order(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, price=price, amount=amount, trade_side=data['side'].upper())
    #    data.update(match_to)
        return data
