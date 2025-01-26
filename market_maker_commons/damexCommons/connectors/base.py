from ccxt.base.exchange import Exchange as CCXTExchange
import time
from abc import abstractmethod
from typing import Callable, Optional
import logging
from websocket import create_connection
from damexCommons.base import Trade, TradeSide, Order, OrderSide, OrderStatus
from damexCommons.tools.dbs import get_exchange_db

class BaseCommons:
    
    def __init__(self, exchange_connector: CCXTExchange, exchange: str, base_asset: str, quote_asset: str):
        self.exchange_connector = exchange_connector
        self.exchange = exchange
        self.base_asset = base_asset
        self.quote_asset = quote_asset
        self.exchange_db = get_exchange_db(db_connection='exchange')
        self.exchange_info: dict = self.exchange_db.fetch_exchanges_info_db(exchanges=[self.exchange])
    
    @property
    def pair(self) -> str:
        return self.base_asset + '-' + self.quote_asset
    
    @property    
    @abstractmethod
    def exchange_pair(self):
        raise NotImplementedError
    
    @property
    def exchange_active_markets(self) -> list[str]:
        return list(self.exchange_info[self.exchange].keys())
    
    @property
    def price_decimals(self) -> int:
        return self.exchange_info[self.exchange][self.pair]['price_decimals']
    
    @property
    def base_amount_decimals(self) -> int:
        return self.exchange_info[self.exchange][self.pair]['base_amount_decimals']
    
    @property
    def quote_amount_decimals(self) -> int:
        return self.exchange_info[self.exchange][self.pair]['quote_amount_decimals']
    
    @property
    def base_min_amount(self) -> int:
        return self.exchange_info[self.exchange][self.pair]['base_min_amount']
    
    @property
    def quote_min_amount(self) -> int:
        return self.exchange_info[self.exchange][self.pair]['quote_min_amount']
    
    @property
    def market_use(self) -> str:
        return self.exchange_info[self.exchange][self.pair]['market_use']
    
    @property
    def exchange_status(self) -> str:
        return self.exchange_info[self.exchange][self.pair]['status_exchange']
    
    @property
    def market_status(self) -> str:
        return self.exchange_info[self.exchange][self.pair]['status_market']
    
    @property
    def exchange_market_status(self) -> str:
        return self.exchange_info[self.exchange][self.pair]['status_exchange_market']
           
    @property
    def buy_fee_percentage(self) -> float:
        return self.exchange_info[self.exchange][self.pair]['buy_fee_percentage'] 
    
    @property
    def buy_fee_asset_type(self) -> float:
        return self.exchange_info[self.exchange][self.pair]['buy_fee_asset_type'] 
    
    @property
    def sell_fee_percentage(self) -> float:
        return self.exchange_info[self.exchange][self.pair]['sell_fee_percentage'] 
           
    @property
    def sell_fee_asset_type(self) -> float:
        return self.exchange_info[self.exchange][self.pair]['sell_fee_asset_type'] 
    
    @property
    def market_main_price_exist(self) -> float:
        return self.exchange_info[self.exchange][self.pair]['market_main_price_exist'] 
        
    @abstractmethod
    async def fetch_balance(self) -> dict:
        raise NotImplementedError
    
    @abstractmethod
    async def fetch_ticker(self) -> dict:
        raise NotImplementedError
    
    @abstractmethod
    async def fetch_tickers(self, markets: list[str]) -> list[dict]:
        raise NotImplementedError


class ExchangeCommons(BaseCommons):
    
    def __init__(self, exchange_connector: CCXTExchange, exchange: str, base_asset: str, quote_asset: str):
        BaseCommons.__init__(
            self,
            exchange_connector,
            exchange,
            base_asset,
            quote_asset
        )
                                
    @abstractmethod
    async def fetch_order_book(self) -> dict:
        raise NotImplementedError
    
    @abstractmethod
    async def create_limit_order(self, side: str, price: float, amount: float) -> str:
        raise NotImplementedError
    
    @abstractmethod
    async def cancel_limit_order(self, order_id: str) -> None:
        raise NotImplementedError
        
    @abstractmethod
    async def fetch_order_status(self, order_id: str) -> OrderStatus:
        raise NotImplementedError
            
    @abstractmethod
    async def fetch_order_trades(self, order_id: str) -> list[Trade]:
        raise NotImplementedError
                
    @abstractmethod
    async def fetch_orders_history(self) -> list[Order]:
        raise NotImplementedError
    
    @abstractmethod
    async def fetch_active_orders(self) -> list[dict]:
        raise NotImplementedError
            
class ExchangeWSSCommons:
    
    def __init__(self, wss_url: str, exchange: str,  wss_object_params: dict, order_book_levels: int = 20, wss_headers: dict = None):
        self.wss_url = wss_url
        self.order_book_levels = order_book_levels
        self.exchange = exchange
        self.wss_object_params = wss_object_params
        self.wss_headers = wss_headers
        self.wss = None
    
    async def run_wss(self, base_asset: str, quote_asset: str, wss_object: str, stop_wss: dict, callback: Callable) -> None:
        ws_id = self.exchange + '__' + base_asset + '-' + quote_asset
        if stop_wss[ws_id]:
            return 
        url_suffix = await self.get_wss_object_params(wss_object=wss_object, wss_type='url_suffix')
        if url_suffix is not None:
            self.wss_url = self.wss_url + url_suffix
        if self.wss is None:
            try:
                if self.wss_headers is None:
                    self.wss = create_connection(self.wss_url)
                else:
                    self.wss = create_connection(self.wss_url, header=self.wss_headers)
            except Exception as e:
                logging.error('------------------------------------------WEBSOCKET PROBLEM %s %s %s %s', self.exchange, base_asset, quote_asset, e)
                raise
        request = await self.get_wss_object_params(wss_object=wss_object, wss_type='request')
        if request is not None:
            self.wss.send(request)
        ping_start_time = None
        ping = await self.get_wss_object_params(wss_object='ping')
        if ping is not None:
            ping_start_time = int(time.time() * 1000)
        message_function = await self.get_wss_object_params(wss_object=wss_object, wss_type='message_function')
        while True:   
            try:
                if stop_wss[ws_id]:
                    break 
                if ping_start_time is not None and int(time.time() * 1000) - (20 * 1000) >= ping_start_time:
                    self.wss.send(ping)
                    ping_start_time = int(time.time() * 1000)
                    logging.info('------------------------------------------SENDING ping %s', self.exchange)
                msg = self.wss.recv()
                data = await message_function(msg=msg)
                await callback(exchange=self.exchange, base_asset=base_asset, quote_asset=quote_asset, data=data)
            except Exception as e:
                logging.error('------------------------------------------WEBSOCKET PROBLEM %s %s %s %s', self.exchange, base_asset, quote_asset, e)
                self.wss.close()
                self.wss = None
                break

    async def get_wss_object_params(self, wss_object: str, wss_type: Optional[str] = None) -> dict:    
        if wss_object not in self.wss_object_params:
            return None
        if wss_type is None:
            return self.wss_object_params[wss_object]
        elif wss_type not in self.wss_object_params[wss_object]:
            return None
        return self.wss_object_params[wss_object][wss_type]
    
    @abstractmethod
    async def message_function_order_book(self, msg: str) -> dict:  
        raise NotImplementedError 
    
    @abstractmethod
    async def message_function_ticker(self, msg: str) -> dict:  
        raise NotImplementedError 
    
            
class LPCommons(BaseCommons):
    
    def __init__(self, exchange_connector: CCXTExchange, exchange: str, base_asset: str, quote_asset: str):
        BaseCommons.__init__(
            self,
            exchange_connector,
            exchange,
            base_asset,
            quote_asset
        )
        
    @abstractmethod
    async def simulate_swap_transaction(self, trade_side: TradeSide, amount: float) -> dict:
        raise NotImplementedError
    
    @abstractmethod
    async def send_swap_transaction(self, trade_side: TradeSide, amount: float, price: float) -> dict:
        raise NotImplementedError
    
    @abstractmethod
    async def fetch_swap_prices(self, trade_side: TradeSide, amount: float) -> dict:
        raise NotImplementedError
            
        
class CLOBCommons(BaseCommons):
    
    def __init__(self, exchange_connector: CCXTExchange, exchange: str, base_asset: str, quote_asset: str):
        BaseCommons.__init__(
            self,
            exchange_connector,
            exchange,
            base_asset,
            quote_asset
        )
        
    @abstractmethod
    async def create_limit_order(self, order_side: OrderSide, price: float, amount: float) -> str:
        raise NotImplementedError
    
    @abstractmethod
    async def cancel_limit_order(self, order_id: str) -> None:
        raise NotImplementedError
    
    @abstractmethod
    async def fetch_orders_history(self) -> list[Order]:
        raise NotImplementedError
    
    @abstractmethod
    async def fetch_trades_history(self) -> list[Trade]:
        raise NotImplementedError
    
    @abstractmethod
    async def fetch_market_price(self) -> float:
        raise NotImplementedError
    