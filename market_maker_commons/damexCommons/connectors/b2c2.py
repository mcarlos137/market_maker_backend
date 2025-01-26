import requests
import logging
import uuid
import datetime
import json
import time
from damexCommons.base import OrderStatus, Trade, Order
from damexCommons.connectors.base import ExchangeCommons, ExchangeWSSCommons

REST_ORDER_CREATE = '/v2/order'
REST_BALANCE = '/balance'

API_URL = 'https://api.uat.b2c2.net/'

DEPTHS = {'BTC': [0.01, 0.5], 'ETH': [0.5, 3]}

class B2C2Commons(ExchangeCommons, ExchangeWSSCommons):
    
    
    def __init__(self, api_token: str, base_asset: str, quote_asset: str):   
        ExchangeCommons.__init__(
            self,
            exchange_connector=None,
            exchange='b2c2',
            base_asset=base_asset,
            quote_asset=quote_asset
        )
        ExchangeWSSCommons.__init__(
            self, 
            wss_url='wss://socket.uat.b2c2.net/quotes', 
            wss_headers=['Authorization: Token %s' % (api_token)],
            exchange='b2c2', 
            wss_object_params={
                'order_book': {
                    'request': '{"event": "subscribe", "instrument": "%s.SPOT", "levels": %s}' % (base_asset.upper() + quote_asset.upper(), DEPTHS[base_asset.upper()]),
                    'message_function': self.message_function_order_book
                },
            },
            order_book_levels=20
        )
        self.api_token = api_token
        
    @property
    def exchange_pair(self) -> str:
        return self.base_asset + self.quote_asset

    def get_headers(self):
        return {'Authorization': 'Token %s' % self.api_token}

    async def fetch_order_book(self) -> dict:
        raise NotImplementedError

    async def create_limit_order(self, side: str, price: float, amount: float) -> str:
        try:
            post_data = {
                'instrument': '%s.SPOT' % (self.exchange_pair),
                'side': side.lower(),
                'quantity': str(amount),
                'client_order_id': str(uuid.uuid4()),
                'price': str(price),
                'order_type': 'FOK',
                'valid_until': datetime.datetime.strftime(datetime.datetime.utcnow() + datetime.timedelta(seconds=10), '%Y-%m-%dT%H:%M:%S.%fZ'),
                'executing_unit': 'risk-adding-strategy',
            }
            response = requests.post(API_URL + REST_ORDER_CREATE, headers=self.get_headers(), json=post_data, timeout=7)
            if int(response.status_code) != 200:
                raise Exception(response.reason)         
            order = response.json()
            logging.info('created limit order %s %s %s %s', self.exchange_pair, side, price, amount)
            return str(order["order_id"])
        except Exception as e:
            raise e

    async def cancel_limit_order(self, order_id: str) -> None:
        raise NotImplementedError
        
    async def fetch_order_status(self, order_id: str) -> OrderStatus:
        raise NotImplementedError
            
    async def fetch_order_trades(self, order_id: str) -> list[Trade]:
        raise NotImplementedError
        
    async def fetch_balance(self) -> dict:
        try:
            response = requests.get(API_URL + REST_BALANCE, headers=self.get_headers(), timeout=7)
            if int(response.status_code) != 200:
                raise Exception(response.reason)         
            data = response.json()
            balance = {}
            for coin in data:
                balance[coin] = {
                    'available': float(data[coin]),
                    'total': float(data[coin])
                }
            logging.info('balance %s', balance)
            return balance
        except Exception as e:
            raise e
                
    async def fetch_orders_history(self) -> list[Order]:
        raise NotImplementedError
        
    async def fetch_ticker(self) -> dict:
        raise NotImplementedError
    
    async def fetch_tickers(self, markets: list[str]) -> list[dict]:
        raise NotImplementedError
    
    async def fetch_active_orders(self) -> list[dict]:
        raise NotImplementedError
    
    async def message_function_order_book(self, msg: str) -> dict:
        obj = json.loads(msg)
        order_book = {'asks': [], 'bids': []}
        if obj['event'] == 'price' and 'levels' in obj:
            for ask in obj['levels']['buy']:
                order_book['asks'].append([ask['price'], ask['quantity']])
            for bid in obj['levels']['sell']:
                order_book['bids'].append([bid['price'], bid['quantity']])
            order_book['time'] = int(obj['timestamp'])
            return order_book        
        return {}