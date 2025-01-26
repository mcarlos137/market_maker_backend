import hmac
import hashlib
import json
import time
import math
import requests
import logging
import random
from damexCommons.base import OrderStatus, Trade, Order
from damexCommons.connectors.base import ExchangeCommons, ExchangeWSSCommons
from damexCommons.tools.exchange import match_trade_order

REST_ACCOUNT = '/spot/accountList'
REST_PRICES = '/v1/ticker/price'
REST_ORDER_CREATE = "/trade/order/place"
REST_ORDER_CANCEL = '/trade/order/cancel'
REST_DEPTH = '/v1/market/depth/%s'
REST_ORDER_INFO = '/v2/trade/order/orderInfo'
REST_TRADE_LIST = '/trade/match/accountMatches'
REST_ORDER_LIST = '/v2/trade/order/active'

API_URL = 'https://api.coinstore.com/api'
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

class CoinstoreCommons(ExchangeCommons, ExchangeWSSCommons):
    
    def __init__(self, api_key: str, api_secret: str, base_asset: str, quote_asset: str):
        ExchangeCommons.__init__(
            self,
            exchange_connector=None,
            exchange='coinstore',
            base_asset=base_asset,
            quote_asset=quote_asset
        )
        ExchangeWSSCommons.__init__(
            self, 
            wss_url='wss://ws.coinstore.com/s/ws', 
            exchange='coinstore', 
            wss_object_params={
                'order_book': {
                    'request': '{"op":"SUB","channel":["%s@depth@%s"],"id":%s}' % (base_asset.lower() + quote_asset.lower(), 20, random.randint(1000, 1300)),
                    'message_function': self.message_function_order_book
                },
                'ticker': {
                    'request': '{"op":"SUB","channel":["%s@ticker"],"id":%s}' % (base_asset.lower() + quote_asset.lower(), random.randint(1000, 1300)),
                    'message_function': self.message_function_ticker
                },
                'trade': {
                    'request': '{"op":"SUB","channel":["%s@trade"],"id":%s}' % (base_asset.lower() + quote_asset.lower(), random.randint(1000, 1300)),
                    'message_function': self.message_function_trade
                }
            },
            order_book_levels=20
        )        
        self.api_key = api_key
        self.api_secret = api_secret

    @property
    def exchange_pair(self) -> str:
        return self.base_asset + self.quote_asset

    async def fetch_order_book(self) -> dict:
        try: 
            endpoint = REST_DEPTH % (self.exchange_pair)
            fetch_order_book_response = requests.get(API_URL + endpoint, timeout=7).json()
            if int(fetch_order_book_response['code']) != 0:
                raise Exception(fetch_order_book_response['message'])
            order_book = {'asks': fetch_order_book_response['data']['a'], 'bids': fetch_order_book_response['data']['b']}
            return order_book
        except Exception as e:
            raise e
        
    async def fetch_ticker(self) -> dict:
        raise NotImplementedError

    async def fetch_tickers(self, _markets: list[str]) -> list[dict]:
        raise NotImplementedError

    async def create_limit_order(self, side: str, price: float, amount: float) -> str:
        try:
            endpoint = REST_ORDER_CREATE
            params = {
                "symbol": self.exchange_pair,
                "side": 'BUY' if side == 'BID' else 'SELL',
                "ordQty": amount,
                "ordPrice": price,
                "ordType": "LIMIT",
                "timestamp": int(time.time() * 1e3)
            }
            rsp = self._request_with_params(POST, endpoint, params)
            if int(rsp['code']) != 0:
                raise Exception(rsp['message'])
            order = rsp['data']
            logging.info('created limit order %s, %s, %s, %s', self.exchange_pair, side, price, amount)
            return str(order["ordId"])
        except Exception as e:
            raise e

    async def cancel_limit_order(self, order_id: str) -> None:
        try:
            endpoint = REST_ORDER_CANCEL
            params = {
                "ordId": order_id,
                "symbol": self.exchange_pair,
            }
            rsp = self._request_with_params(POST, endpoint, params)
            if int(rsp['code']) != 0:
                raise Exception(rsp['message'])
            cancel_limit_order_response = rsp['data']
            if cancel_limit_order_response['state'] != "CANCELED":
                raise Exception('failed at cancelling order %s %s' % order_id, self.exchange_pair)
            logging.info('cancelled limit order %s %s', self.exchange_pair, order_id)
        except Exception as e:
            logging.info('failed at cancelling order %s %s %s', order_id, self.exchange_pair, e)
        
    async def fetch_order_status(self, order_id: str) -> OrderStatus:
        try:
            #logging.info('order status %s %s', self.exchange_pair, order_id)
            endpoint = REST_ORDER_INFO
            params = {'ordId': int(order_id)}
            rsp = self._request_with_params(GET, endpoint, params)
            if int(rsp['code']) != 0:
                raise Exception(rsp['message'])
            order = rsp['data']
            #logging.info('fetch_order_status order %s %s', order_id, order)
            status = order['ordStatus']
            #logging.info('fetch_order_status order status %s %s', order_id, status)
            match status:
                case 'SUBMITTED':
                        return OrderStatus.CREATED
                case 'CANCELED':
                    return OrderStatus.CANCELLED
                case 'PARTIAL_FILLED':
                    return OrderStatus.PARTIALLY_FILLED
                case 'FILLED':
                    return OrderStatus.FILLED
                case _:
                    return OrderStatus.FAILED
        except Exception as e:
            raise e
            
    async def fetch_order_trades(self, order_id: str) -> list[Trade]:
        try:
            endpoint = REST_TRADE_LIST
            params = {'symbol': self.exchange_pair, 'pageSize': 100}
            rsp = self._request_with_params(GET, endpoint, params)
            if int(rsp['code']) != 0:
                raise Exception(rsp['message'])
            data = rsp['data']
            trades: list[Trade] = []
            for order_trade in data:
                if int(order_id) != int(order_trade['orderId']):
                    continue
                amount = round(order_trade['execQty'], 1)
                price = round(order_trade['execAmt'] / amount, 6)
                trade_id = str(order_trade['tradeId'])
                fee = {'cost': order_trade['fee'], 'currency': 'USDT'} #PROBLEM
                trades.append({'timestamp': int(order_trade['matchTime'] * 1e3), 'side': 'buy' if order_trade['side'] == 1 else 'sell', 'price': price, 'amount': amount, 'fee': fee, 'id': trade_id})
            logging.info('order trades %s %s %s', self.exchange_pair, order_id, trades)
            return trades 
        except Exception as e:
            raise e
        
    async def fetch_balance(self) -> dict:
        try:
            endpoint = REST_ACCOUNT
            params = {}
            rsp = self._request_with_params(POST, endpoint, params)
            if int(rsp['code']) != 0:
                raise Exception(rsp['message'])
            data = rsp['data']
            balance = {}
            currencies = []
            for coin in data:
                if coin['typeName'] in ['FROZEN', 'AVAILABLE']:
                    currencies.append(coin['currency'])
            currencies = list(set(currencies))
            for currency in currencies:
                if not len([i for i in self.exchange_active_markets if currency in i]) > 0:
                    continue
                balance[currency] = {}
                for coin in data:
                    if coin['currency'] == currency:
                        if coin['typeName'] == "AVAILABLE":
                            balance[currency]['available'] = coin['balance']
                        elif coin['typeName'] == "FROZEN":
                            balance[currency]['frozen'] = coin['balance']
                balance[currency]['total'] = str(float(balance[currency]['available']) + float(balance[currency]['frozen']))
            logging.info('balance %s', balance)
            return balance
        except Exception as e:
            raise e
        
    async def message_function_order_book(self, msg: dict) -> dict:  
        obj = json.loads(msg)
        if obj['T'] == 'depth':
            order_book_time = int(time.time() * 1000)
            return {
                'time': order_book_time,
                'asks': list(map(lambda l: l[:2], obj['a'])),
                'bids': list(map(lambda l: l[:2], obj['b'])),
            }
        return {}
    
    async def message_function_ticker(self, msg: str) -> dict:
        obj = json.loads(msg)
        if obj['T'] == 'ticker':
            ticker_time = int(time.time() * 1000)
            return {
                'time': ticker_time,
                'lastPrice': float(obj['close']),
                'volume': float(obj['amount']),
                'high': float(obj['high']),
                'low': float(obj['low']),
            }
        return {}
    
    async def message_function_trade(self, msg: str) -> dict:
        obj = json.loads(msg)
        data = {}
        if obj['T'] == 'trade' and 'channel' in obj:
            data['time'] = int(obj['ts'])
            data['price'] = float(obj['price'])
            data['amount'] = float(obj['volume'])
            data['currency'] = self.base_asset
            data['side'] = str(obj['takerSide']).lower()
            data['exchange'] = self.exchange
            price = data['price']
            amount = data['amount']
            time.sleep(5)
            match_to = await match_trade_order(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, price=price, amount=amount, trade_side=data['side'].upper())
            data.update(match_to)
            return data
        return data
            
    async def fetch_orders_history(self) -> list[Order]:
        raise NotImplementedError
    
    async def fetch_active_orders(self) -> list[dict]:
        try:
            endpoint = REST_ORDER_LIST
            params = {'symbol': self.exchange_pair}
            rsp = self._request_with_params(GET, endpoint, params)
            if int(rsp['code']) != 0:
                raise Exception(rsp['message'])
            return rsp['data'] 
        except Exception as e:
            raise e
        
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
            raise response.json()
        return response.json()

    def get_sign(self, params, method, timestamp):
        expires = timestamp
        expires_key = str(math.floor(expires / 30000))
        expires_key = expires_key.encode("utf-8")
        secret_key = self.api_secret.encode("utf-8")
        key = hmac.new(secret_key, expires_key, hashlib.sha256).hexdigest()
        key = key.encode("utf-8")
        if method == GET:
            params = parse_params_to_str(params)
            params = params[1:]
        else:
            params = json.dumps(params)
        payload = params.encode("utf-8")
        signature = hmac.new(key, payload, hashlib.sha256).hexdigest()
        header = {
            "X-CS-APIKEY": self.api_key,
            "X-CS-EXPIRES": str(expires),
            "X-CS-SIGN": signature,
            'Content-Type': 'application/json',
        }
        return expires, signature, header
