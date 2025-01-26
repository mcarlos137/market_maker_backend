import hmac
import hashlib
import json
import time
import base64
import requests
import logging
import random
from datetime import datetime
from damexCommons.base import OrderStatus, Order, Trade
from damexCommons.connectors.base import ExchangeCommons, ExchangeWSSCommons
from damexCommons.tools.exchange import match_trade_order


REST_ACCOUNT = '/api/v1/account/balances'
REST_ORDER_CREATE = '/api/v1/order/new'
REST_ORDER_CANCEL = '/api/v1/order/cancel'
REST_ORDER_LIST = '/api/v1/orders'
REST_ORDER_TRADES = '/api/v1/account/trades'
REST_DEPTH = '/api/v1/public/depth/result'
REST_ORDER_HISTORY = "/api/v1/account/order_history"

API_URL = 'https://api.tidex.com'
CONTENT_TYPE = 'Content-Type'

APPLICATION_FORM = 'application/x-www-form-urlencoded'

GET = "GET"
POST = "POST"
DELETE = "DELETE"

def get_timestamp():
    timestamp = int(time.time() * 1000)
    return timestamp

def parse_params_to_str(params):
    url = '?'
    for key, value in params.items():
        url = url + str(key) + '=' + str(value) + '&'
    return url[0:-1]

def get_header():
    header = dict()
    header[CONTENT_TYPE] = APPLICATION_FORM
    return header

class TidexCommons(ExchangeCommons, ExchangeWSSCommons):
    
    def __init__(self, api_key: str, api_secret: str, base_asset: str, quote_asset: str):
        ExchangeCommons.__init__(
            self,
            exchange_connector=None,
            exchange='tidex',
            base_asset=base_asset,
            quote_asset=quote_asset
        )
        ExchangeWSSCommons.__init__(
            self, 
            wss_url='wss://ws.tidex.com', 
            exchange='tidex', 
            wss_object_params={
                'ping': '{"method":"server.ping", "params": [], "id":%s}' % (random.randint(10000, 13000)),
                'order_book': {
                    'request': '{"method":"depth.subscribe", "params": ["%s_%s", %s, "0"], "id":%s}' % (base_asset, quote_asset, 20, random.randint(10000, 13000)),
                    'message_function': self.message_function_order_book
                },
                'ticker': {
                    'request': '{"method":"kline.subscribe", "params": ["%s_%s", 86400], "id":%s}' % (base_asset, quote_asset, random.randint(10000, 13000)),
                    'message_function': self.message_function_ticker
                },
                'trade': {
                    'request': '{"method":"deals.subscribe", "params": ["%s_%s"], "id":%s}' % (base_asset, quote_asset, random.randint(10000, 13000)),
                    'message_function': self.message_function_trade
                }
            },
            order_book_levels=20
        )
        self.api_key = api_key
        self.api_secret = api_secret
        self.thread_tickets = []
        
    @property
    def exchange_pair(self) -> str:
        return self.base_asset + '_' + self.quote_asset
    
    async def fetch_order_book(self) -> dict:
        thread_ticket = ''.join(random.choice('0123456789ABCDEF') for i in range(16))
        self.thread_tickets.append(thread_ticket)
        while True:
            time.sleep(1)
            if self.thread_tickets[0] == thread_ticket:
                break
        try: 
            endpoint = REST_DEPTH
            params = {
                "request": endpoint,
                "nonce": str(int(datetime.now().timestamp() * 1000)),
                "market": self.exchange_pair,
                "limit": 10,
            }
            fetch_order_book_response = self._request_with_params(POST, endpoint, params)
            fetch_order_book_response['bids'].reverse()
            order_book = {'asks': fetch_order_book_response['asks'], 'bids': fetch_order_book_response['bids']}
            return order_book
        except Exception as e:
            raise e
        finally:
            time.sleep(1)
            self.thread_tickets.pop(0)

    async def create_limit_order(self, side: str, price: float, amount: float) -> str:
        thread_ticket = ''.join(random.choice('0123456789ABCDEF') for i in range(16))
        self.thread_tickets.append(thread_ticket)
        while True:
            time.sleep(1)
            if self.thread_tickets[0] == thread_ticket:
                break
        try:
            endpoint = REST_ORDER_CREATE
            params = {
                "request": endpoint,
                "nonce": str(int(datetime.now().timestamp() * 1000)),
                "market": self.exchange_pair,
                "price": str(price),
                "amount": str(amount),
                "side": 'buy' if str(side).lower() == 'bid' else 'sell'
            }
            create_limit_order_response = self._request_with_params(POST, endpoint, params)
            if not create_limit_order_response['success']:
                raise Exception('failed at creating order %s %s %s %s' % (self.exchange_pair, side, price, amount))
            order = create_limit_order_response['result']            
            logging.info('created limit order %s %s %s %s', self.exchange_pair, side, price, amount)
            return str(order["orderId"])
        
        except Exception as e:
            raise e
        finally:
            time.sleep(1)
            self.thread_tickets.pop(0)
    
    async def cancel_limit_order(self, order_id: str) -> None:
        thread_ticket = ''.join(random.choice('0123456789ABCDEF') for i in range(16))
        self.thread_tickets.append(thread_ticket)
        while True:
            time.sleep(1)
            if self.thread_tickets[0] == thread_ticket:
                break
        try:
            endpoint = REST_ORDER_CANCEL
            params = {
                "request": endpoint,
                "nonce": str(int(datetime.now().timestamp() * 1000)),
                "market": self.exchange_pair,
                "orderId": int(order_id)
            }
            cancel_limit_order_response = self._request_with_params(POST, endpoint, params)
            if not cancel_limit_order_response['success']:
                raise Exception('failed at cancelling order %s %s' % (order_id, self.exchange_pair))
            logging.info('cancelled limit order %s %s', self.exchange_pair, order_id)     
        except Exception as e:
            if e.args[0] != REST_ORDER_CANCEL:
                raise e
        finally:
            time.sleep(1)
            self.thread_tickets.pop(0)
        
    async def fetch_active_orders(self) -> list[dict]:
        thread_ticket = ''.join(random.choice('0123456789ABCDEF') for i in range(16))
        self.thread_tickets.append(thread_ticket)
        while True:
            time.sleep(1)
            if self.thread_tickets[0] == thread_ticket:
                break
        try:
            endpoint = REST_ORDER_LIST
            params = {
                "request": endpoint,
                "nonce": str(int(datetime.now().timestamp() * 1000)),
                "market": self.exchange_pair,
                "limit": 100
            }
            fetch_order_status_response = self._request_with_params(POST, endpoint, params)
            if not fetch_order_status_response['success']:
                raise Exception('failed at getting orders %s', self.exchange_pair)
            return fetch_order_status_response['result']['result']
        except Exception as e:
            raise e
        finally:
            time.sleep(1)
            self.thread_tickets.pop(0)
            
    async def fetch_orders_history(self) -> list[Order]:
        thread_ticket = ''.join(random.choice('0123456789ABCDEF') for i in range(16))
        self.thread_tickets.append(thread_ticket)
        while True:
            time.sleep(1)
            if self.thread_tickets[0] == thread_ticket:
                break
        try:
            endpoint = REST_ORDER_HISTORY
            params = {
                "request": endpoint,
                "nonce": str(int(datetime.now().timestamp() * 1000)),
                "limit": 100
            }
            resp = self._request_with_params(POST, endpoint, params)
            if not resp['success']:
                raise Exception(f'failed at getting orders')
            return resp['result'][self.exchange_pair]
        except Exception as e:
            raise e
        finally:
            time.sleep(1)
            self.thread_tickets.pop(0)
        
    async def fetch_balance(self) -> dict:
        thread_ticket = ''.join(random.choice('0123456789ABCDEF') for i in range(16))
        self.thread_tickets.append(thread_ticket)
        while True:
            time.sleep(1)
            if self.thread_tickets[0] == thread_ticket:
                break
        try:
            endpoint = REST_ACCOUNT
            params = {
                "request": endpoint,
                "nonce": str(int(datetime.utcnow().timestamp() * 1000))
            }
            fetch_balance_response = self._request_with_params(POST, endpoint, params)
            balance = dict()
            currencys = []
            for coin in fetch_balance_response['result']:
                if not len([i for i in self.exchange_active_markets if coin in i]) > 0:
                    continue
                currencys.append(coin)
            currencys = list(set(currencys))
            for currency in currencys:
                balance[currency] = {}
                for coin in fetch_balance_response['result']:
                    if coin == currency:
                        balance[currency]['available'] = fetch_balance_response['result'][coin]['available']
                        balance[currency]['used'] = fetch_balance_response['result'][coin]['freeze']

                balance[currency]['total'] = str(float(balance[currency]['available']) + float(balance[currency]['used']))
            logging.info('balance %s', balance)
            return balance
        except Exception as e:
            raise e
        finally:
            time.sleep(1)
            self.thread_tickets.pop(0)
            
    async def fetch_ticker(self) -> dict:
        raise NotImplementedError

    async def fetch_tickers(self, markets: list[str]) -> list[dict]:
        raise NotImplementedError
        
    async def message_function_order_book(self, msg: dict) -> dict:  
        obj = json.loads(msg)
        if not 'method' in obj:
            return {}
        method = obj['method']
        if method == 'depth.update':
            if not 'asks' in obj['params'][1] or not 'bids' in obj['params'][1]:
                    return {}
            asks = [item for item in obj['params'][1]['asks'] if float(item[1]) > 0]
            bids = [item for item in obj['params'][1]['bids'] if float(item[1]) > 0]
            bids.sort(key=lambda order: float(order[0]), reverse=True)
            if len(asks) > 0 and len(bids) > 0:
                order_book_time = int(time.time() * 1000)
                return {
                    'time': order_book_time,
                    'asks': asks,
                    'bids': bids,
                }        
        return {}
    
    async def message_function_ticker(self, msg: str) -> dict:
        obj = json.loads(msg)
        if not 'method' in obj:
            return {}
        method = obj['method']
        if method == 'kline.update':
            values = str(obj['params'])[1:][:-1][1:][:-1].replace("'", "").split(', ')
            if len(values) < 8:
                return {}
            ticker_time = int(time.time() * 1000)
            return {
                'time': ticker_time,
                'lastPrice': float(values[2]),
                'volume': float(values[6]),
                'high': float(values[3]),
                'low': float(values[4]),
            }
        return {}
    
    async def message_function_trade(self, msg: str) -> dict:
        obj = json.loads(msg)
        if not 'method' in obj:
            return {}
        if len(obj['params'][1]) > 1:
            return {}
        data = {}
        values = obj['params'][1][0]
        data['time'] = int(values['time'] * 1e3)
        data['price'] = float(values['price'])
        data['amount'] = float(values['amount'])
        data['currency'] = self.base_asset
        data['side'] = str(values['type'])
        data['exchange'] = self.exchange
        price = data['price']
        amount = data['amount']
        time.sleep(5)
        match_to = await match_trade_order(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, price=price, amount=amount, trade_side=data['side'].upper())
        data.update(match_to)
        return data
        
    async def fetch_order_status(self, order_id: str) -> OrderStatus:
        raise NotImplementedError
            
    async def fetch_order_trades(self, order_id: str) -> list[Trade]:
        raise NotImplementedError
    
    #############################           
    def _request_with_params(self, method, request_path, params):
        return self._request(method, request_path, params)
    
    def _request(self, method, request_path, params, sign_flag=True):
        header = get_header()
        if sign_flag:
            timestamp = get_timestamp()
            expires, sign, header = self.get_sign(params, method, timestamp)
        if method == GET:
            request_path = request_path + parse_params_to_str(params)
        url = API_URL + request_path
        body = params if method == POST else {}

        response = None
        if method == GET:
            response = requests.get(url, headers=header, timeout=7)
        elif method == POST:
            response = requests.post(url, data=json.dumps(body), headers=header, timeout=7)
        elif method == DELETE:
            response = requests.delete(url, headers=header, timeout=7)        
                
        if not str(response.status_code).startswith('2'):
            raise ValueError(request_path, response.json())
        return response.json()

    def get_sign(self, params, method, timestamp):
        payload = base64.b64encode(json.dumps(params).encode("utf-8"))
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            payload,
            hashlib.sha512).hexdigest()
        
        header = {
            'Content-type': 'application/json',
            'X-TXC-APIKEY': self.api_key,
            'X-TXC-PAYLOAD': payload,
            'X-TXC-SIGNATURE': signature        
        }
        return 0, signature, header
        