from ccxt.base.exchange import Exchange as CCXTExchange
import logging
import time
import random
import json
from damexCommons.connectors.base import ExchangeWSSCommons
from damexCommons.connectors.ccxt import CCXTCommons
from damexCommons.tools.exchange import match_trade_order

class BitfinexCommons(CCXTCommons, ExchangeWSSCommons):
    
    def __init__(self, exchange_connector: CCXTExchange, base_asset: str, quote_asset: str):
        CCXTCommons.__init__(
            self, 
            exchange_connector=exchange_connector, 
            exchange='bitfinex',
            base_asset=base_asset, 
            quote_asset=quote_asset
        )
        ExchangeWSSCommons.__init__(
            self, 
            wss_url='wss://api-pub.bitfinex.com/ws/2', 
            exchange='bitfinex', 
            wss_object_params={
                'ping': '{"event":"ping", "cid": %s}' % (random.randint(10000, 13000)),
                'order_book': {
                    'request': '{"event":"subscribe","channel":"book","symbol":"t%s","prec":"P0","freq":"F0","len":"25","subId": %s}' % (base_asset + quote_asset, random.randint(100000, 130000)),
                    'message_function': self.message_function_order_book
                },
                'ticker': {
                    'request': '{"event":"subscribe","channel":"ticker","symbol":"t%s","subId": %s}' % (base_asset + quote_asset, random.randint(100000, 130000)),
                    'message_function': self.message_function_ticker
                },
                'trade': {
                    'request': '{"event":"subscribe","channel":"trades","symbol":"t%s","subId": %s}' % (base_asset + quote_asset, random.randint(100000, 130000)),
                    'message_function': self.message_function_trade
                }
            },
            order_book_levels=20
        )
        self.order_book = {'asks': [], 'bids': []}
        
    async def fetch_balance(self) -> dict:
        try:
            balance_response = self.exchange_connector.fetch_balance()
            balance = {}
            for b in balance_response:
                if not len([i for i in self.exchange_active_markets if b in i]) > 0:
                    continue
                balance[b] = {'available': float(balance_response[b]['free']), 'total': float(balance_response[b]['total'])}
            logging.info('balance %s', balance)
            return balance
        except Exception as e:
            raise e
    
    async def message_function_order_book(self, msg: str) -> dict:
        obj = json.loads(msg)
        if 'event' in obj or 'hb' in obj:
            return {}
        if len(obj[1]) == 50:
            for order in obj[1]:
                price = order[0]
                amount = order[2]
                if amount < 0:
                    amount *= -1
                    self.order_book['asks'].append([price, amount])
                else:
                    self.order_book['bids'].append([price, amount])
        else:
            order = obj[1]
            price = order[0]
            quantity = order[1]
            amount = order[2]
            if quantity > 0:
                if amount < 0:
                    amount *= -1
                    self.order_book['asks'].append([price, amount])
                else:
                    self.order_book['bids'].append([price, amount])
            else:
                self.order_book['asks'] = [item for item in self.order_book['asks'] if float(price) != float(item[0])]
                self.order_book['bids'] = [item for item in self.order_book['bids'] if float(price) != float(item[0])]
        self.order_book['asks'].sort(key=lambda order: float(order[0]), reverse=False)
        self.order_book['bids'].sort(key=lambda order: float(order[0]), reverse=True)
        self.order_book['asks'] = self.order_book['asks'][:20]
        self.order_book['bids'] = self.order_book['bids'][:20]
        return self.order_book

    async def message_function_ticker(self, msg: str) -> dict:
        obj = json.loads(msg)
        if type(obj) == list and obj[1] != 'hb':
            ticker_time = int(time.time() * 1000)
            return {
                'time': ticker_time,
                'lastPrice': float(obj[1][6]),
                'volume': float(obj[1][7] * (obj[1][8] + obj[1][9]) / 2),
                'high': float(obj[1][8]),
                'low': float(obj[1][9]),
            }
        return {}
    
    async def message_function_trade(self, msg: str) -> dict:
        obj = json.loads(msg)
        data = {}
        if type(obj) == list and obj[1] != 'hb' and obj[1] in ['te', 'tu', 'fte', 'ftu']:
            amount = float(abs(obj[2][2]))
            side = 'SELL' if obj[2][2] < 0 else 'BUY'
            data['time'] = int(obj[2][1])
            data['price'] = float(obj[2][3])
            data['amount'] = amount
            data['currency'] = self.base_asset
            data['side'] = side
            data['exchange'] = self.exchange
            print('data----------', data)
            #price = data['price']
            #time.sleep(5)
            #match_to = await match_trade_order(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, price=price, amount=amount, trade_side=data['side'].upper())
            #data.update(match_to)
            return data
        return data
    