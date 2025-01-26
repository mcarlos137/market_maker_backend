import random
from enum import Enum
from typing import Any, Dict, NamedTuple, Optional
import time
import json

class OrderSide(Enum):
    ASK = 1
    BID = 2
    
    @staticmethod
    def from_str(label: str):
        if label in ('ASK'):
            return OrderSide.ASK
        elif label in ('BID'):
            return OrderSide.BID
        else:
            raise NotImplementedError
    
class OrderType(Enum):
    LIMIT = 1
    MARKET = 2
        
class OrderStatus(Enum):
    CREATED = 1
    CANCELLED = 2
    PARTIALLY_FILLED = 3
    FILLED = 4
    PENDING_TO_CREATE = 5
    PENDING_TO_CANCEL = 6
    FAILED = 7

class TradeSide(Enum):
    BUY = 1
    SELL = 2   
    
    @staticmethod
    def from_str(label: str):
        if label in ('BUY'):
            return TradeSide.BUY
        elif label in ('SELL'):
            return TradeSide.SELL
        else:
            raise NotImplementedError
    
class Order:
    def __init__(self,
                id: str,
                bot_id: str,
                strategy_id: str,
                base_asset: str,
                quote_asset: str,
                creation_timestamp: int,
                type: OrderType,
                price: float,
                amount: float,
                last_status: OrderStatus,
                last_update_timestamp: int,
                side: OrderSide,
                exchange_id: Optional[str] = None,
                exchange: str = None
                #trades: Optional[List[Trade]] = []
                ):
        self.id = id
        self.bot_id = bot_id
        self.strategy_id = strategy_id
        self.base_asset = base_asset
        self.quote_asset = quote_asset
        self.creation_timestamp = creation_timestamp
        self.type = type
        self.price = price
        self.amount = amount
        self.last_status = last_status
        self.last_update_timestamp = last_update_timestamp
        self.side = side
        self.exchange_id = exchange_id
        self.exchange = exchange
        #self.trades = trades
        
    def __str__(self):
        return f'order {self.id} {self.bot_id} {self.strategy_id} {self.base_asset}-{self.quote_asset} {self.creation_timestamp} {self.type} {self.price} {self.amount} {self.last_status} {self.last_update_timestamp} {self.side} {self.exchange_id} {self.exchange}'
        
    @property
    def is_created(self) -> bool:
        return self.exchange_id != None
        
    @classmethod
    def from_json(cls, data: Dict[str, Any]):
        instance = Order(
            id=data["id"],
            bot_id=data["bot_id"],
            strategy_id=data["strategy_id"],
            base_asset=data["base_asset"],
            quote_asset=data["quote_asset"],
            creation_timestamp=data["creation_timestamp"],
            type=OrderType(data["type"]),
            price=float(data["price"]),
            amount=float(data["amount"]),
            last_status=OrderStatus(data["last_status"]),
            last_update_timestamp=data["last_update_timestamp"],
            exchange_id=data["exchange_id"],
            side=OrderSide(data["side"]),
            exchange=data["exchange"]
        )
        return instance

    def to_json(self) -> Dict[str, Any]:
        json_dict = self._asdict()
        json_dict.update({
            "price": str(self.price),
            "amount": str(self.amount),
            "type": self.type.name,
            "last_status": self.last_status.name,
            "side": self.side.name
        })
        return json_dict

    
balance_1h_start = None
balance_1h_timestamp = None

strategy = {
    'trade_amount_limit_1h': {'SELL': 10000, 'BUY': 2000},
    'spread': {'ASK': 0.1, 'BID': 0.1},
    'order_amount': {'ASK': 100, 'BID': 100},
    'order_levels': {'ASK': 10, 'BID': 10},
    'order_level_spread': {'ASK': 0.2, 'BID': 0.1},
    'order_level_amount': {'ASK': 20, 'BID': 15},
    'id': 'maker_test_v1'
    }
order_refresh_timestamp = {'ASK': None, 'BID': None}

#print(random.uniform(0, 10))

main_price = 0.048
price_decimals = 0
amount_decimals = 2
exchange = 'test'
base_asset = 'DAMEX'
quote_asset = 'USDT'
bot_id = 111

sides = ['BID', 'ASK']

def fetch_balance():
    with open('balance.json', 'r') as file:
        return json.load(file)


while True:
    
    timestamp = int(time.time() * 1e3)
    if balance_1h_timestamp is None or timestamp - (3 * 60 * 1e3) > balance_1h_timestamp:
        balance_1h_timestamp = timestamp
        balance = fetch_balance()
        available_base_amount = float(balance[base_asset]['available'])
        available_quote_amount = float(balance[quote_asset]['available'])
        balance_1h_start = {base_asset: available_base_amount, quote_asset: available_quote_amount}
            
    orders_to_create = {OrderSide.ASK.name: [], OrderSide.BID.name: []}
    
    for side in sides:
        order_refresh_timestamp[side] = int(time.time() * 1e3)
        i = 0
        spread = strategy['spread'][side]
        amount = round(strategy['order_amount'][side], price_decimals)
        total_amount = amount
        while i < strategy['order_levels'][side]:
            i += 1    
            price = (main_price - (main_price * spread / 100)) if side == OrderSide.BID.name else (main_price + (main_price * spread / 100))
            price = round(price, price_decimals)
            timestamp = int(time.time() * 1e3)
            id = ''.join(random.choice('0123456789ABCDEF') for i in range(16))
            order_to_create = Order(
                id=id, 
                bot_id=bot_id, 
                strategy_id=strategy['id'], 
                base_asset=base_asset, 
                quote_asset=quote_asset,
                creation_timestamp=timestamp,
                type=OrderType.LIMIT,
                price=float(price),
                amount=float(amount),
                last_status=OrderStatus.PENDING_TO_CREATE,
                last_update_timestamp=int(time.time() * 1e3),
                side=OrderSide.from_str(side),
                exchange=exchange
            )       
            orders_to_create[side].append(order_to_create)
            spread += strategy['order_level_spread'][side]
            amount += round(strategy['order_level_amount'][side], amount_decimals)
            total_amount += amount
            balance = fetch_balance()
            available_base_amount = float(balance[base_asset]['available'])
            available_quote_amount = float(balance[quote_asset]['available'])
            
            print('available_base_amount', available_base_amount)
            print('available_quote_amount', available_quote_amount)
            print('balance_1h_start', balance_1h_start)
            
            if side == 'ASK':
                base_asset_diff = balance_1h_start[base_asset] - available_base_amount
                if base_asset_diff + total_amount >= strategy['trade_amount_limit_1h'][TradeSide.SELL.name]:
                    excluded_order = orders_to_create['ASK'].pop()
                    break
            elif side == 'BID':
                quote_asset_diff = balance_1h_start[quote_asset] - available_quote_amount
                if quote_asset_diff + (total_amount * main_price) >= (strategy['trade_amount_limit_1h'][TradeSide.BUY.name] * main_price):
                    excluded_order = orders_to_create[OrderSide.BID.name].pop()
                    break
            
    print('orders_to_create ASK', orders_to_create['ASK'], len(orders_to_create['ASK']))
    print('orders_to_create BID', orders_to_create['BID'], len(orders_to_create['BID']))
            
    time.sleep(2)