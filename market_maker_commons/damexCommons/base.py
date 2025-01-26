from typing import Dict, Any, NamedTuple, Optional
from enum import Enum


EXCHANGE_USE = {
    1: 'mm',
    2: 'trading',
    3: 'mm_and_trading'
}

STATUS = {
    1: 'active',
    2: 'inactive'
}

FEE_ASSET_TYPE = {
    1: 'base',
    2: 'quote'
}

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
        
    @staticmethod
    def from_id(id: int):
        if id == 1:
            return OrderSide.ASK
        elif id == 2:
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
    
    
class Trade(NamedTuple):
    bot_id: str
    strategy_id: str
    base_asset: str
    quote_asset: str
    timestamp: int
    order_id: str
    side: TradeSide
    price: float
    amount: float
    fee: dict
    exchange_id: str
    exchange: str
    
    @property
    def is_created(self) -> bool:
        return self.exchange_id is not None
        
    @classmethod
    def from_json(cls, data: Dict[str, Any]):
        instance = Trade(
            bot_id=data["bot_id"],
            strategy_id=data["strategy_id"],
            base_asset=data["base_asset"],
            quote_asset=data["quote_asset"],
            timestamp=data["timestamp"],
            order_id=data["order_id"],
            side=TradeSide(data["side"]),
            price=float(data["price"]),
            amount=float(data["amount"]),
            fee={},
            exchange_id=data["exchange_id"],
            exchange=data["exchange"]
        )
        return instance

    @classmethod
    def to_json(self) -> Dict[str, Any]:
        json_dict = self.__dict__
        json_dict.update({
            "price": str(self.price),
            "amount": str(self.amount),
            "side": self.side.name,
        })
        return json_dict

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
                aux: Optional[bool] = False,
                exchange_id: Optional[str] = None,
                exchange: str = None,
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
        self.aux = aux
        #self.trades = trades
        
    def __str__(self):
        return f'order {self.id} {self.bot_id} {self.strategy_id} {self.base_asset}-{self.quote_asset} {self.creation_timestamp} {self.type} {self.price} {self.amount} {self.last_status} {self.last_update_timestamp} {self.side} {self.exchange_id} {self.exchange} {self.aux}'
        
    @property
    def is_created(self) -> bool:
        return self.exchange_id is not None
    
    @property
    def commons_exchange(self) -> bool:
        if self.aux:
            return self.exchange + '_aux'
        return self.exchange
        
    @classmethod
    def from_json(cls, data: dict[str, Any]):
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
            exchange=data["exchange"],
            aux=data["aux"]
        )
        return instance

    @classmethod
    def to_json(self) -> dict[str, Any]:
        json_dict = self.__dict__
        json_dict.update({
            "price": str(self.price),
            "amount": str(self.amount),
            "type": self.type.name,
            "last_status": self.last_status.name,
            "side": self.side.name
        })
        return json_dict

class CcxtOrderShortDetails(NamedTuple):
    price: float
    filled: float
    remaining: float
    fee: Any
            
    @classmethod
    def from_json(cls, data: Dict[str, Any]):
        instance = CcxtOrderShortDetails(
            price=data["price"],
            filled=data["filled"],
            remaining=data["remaining"],
            fee=data["fee"]
        )
        return instance

    @classmethod
    def to_json(self) -> Dict[str, Any]:
        return self.__dict__
