import logging
from ccxt.base.exchange import Exchange as CCXTExchange
from damexCommons.base import OrderStatus, Trade, Order, CcxtOrderShortDetails
from damexCommons.connectors.base import ExchangeCommons


class CCXTCommons(ExchangeCommons):
    
    def __init__(self, exchange_connector: CCXTExchange, exchange: str, base_asset: str, quote_asset: str):
        ExchangeCommons.__init__(
            self,
            exchange_connector=exchange_connector,
            exchange=exchange,
            base_asset=base_asset,
            quote_asset=quote_asset,
        )
        
    @property
    def exchange_pair(self) -> str:
        return self.base_asset + '/' + self.quote_asset

    async def fetch_order_book(self) -> dict:
        try: 
            return self.exchange_connector.fetch_l2_order_book(self.exchange_pair)
        except Exception as e:
            raise e
        
    async def fetch_ticker(self) -> dict:
        try: 
            return self.exchange_connector.fetch_ticker(self.exchange_pair)
        except Exception as e:
            raise e
        
    async def fetch_tickers(self, markets: list[str]) -> list[dict]:
        try: 
            return self.exchange_connector.fetch_tickers(markets)
        except Exception as e:
            raise e

    async def create_limit_order(self, side: str, price: float, amount: float) -> str:
        try:
            order = self.exchange_connector.create_limit_order(symbol=self.exchange_pair, side='sell' if side == 'ASK' else 'buy', amount=amount, price=price)
            logging.info('created limit order %s %s %s %s', self.exchange_pair, side, price, amount)
            return order["id"]
        except Exception as e:
            raise e

    async def cancel_limit_order(self, order_id: str) -> None:
        try:
            self.exchange_connector.cancel_order(id=order_id, symbol=self.exchange_pair)
            logging.info('cancelled limit order %s %s', self.exchange_pair, order_id)
        except Exception as e:
            logging.error('failed at cancelling order %s %s %s', order_id, self.exchange_pair, e)
        
    async def fetch_order_status(self, order_id: str) -> OrderStatus:
        try:
            order = self.exchange_connector.fetch_order(id=order_id, symbol=self.exchange_pair)
            status = order['status']
            amount = order['amount']
            remaining_amount = order['remaining']
            order_status: OrderStatus = OrderStatus.FAILED
            match status:
                case 'open':
                    if amount == remaining_amount:
                        order_status = OrderStatus.CREATED
                    else:
                        order_status = OrderStatus.PARTIALLY_FILLED
                case 'canceled':
                    order_status = OrderStatus.CANCELLED
                case 'closed':
                    order_status = OrderStatus.FILLED
            #logging.info('order status %s %s %s', self.exchange_pair, order_id, order_status)
            return order_status
        except Exception as e:
            raise e
            
    async def fetch_order_trades(self, order_id: str) -> list[Trade]:
        try:
            trades = self.exchange_connector.fetch_order_trades(id=order_id, symbol=self.exchange_pair)
            logging.info('order trades %s %s %s', self.exchange_pair, order_id, trades)
            return trades
        except Exception as e:
            raise e
    
    async def fetch_ccxt_order_filled_short_details(self, order_id: str) -> dict:
        try:
            order_info = self.exchange_connector.fetch_order(id=order_id)   
            return {
                'price': float(order_info['price']),
                'filled': float(order_info['filled']),
                'remaining': float(order_info['remaining']),
                'fee': order_info['fee']
            }
        except Exception as e:
            raise e  
    
    async def fetch_balance(self) -> dict:
        raise NotImplementedError
            
    async def fetch_orders_history(self) -> list[Order]:
        raise NotImplementedError
    
    async def fetch_active_orders(self) -> list[dict]:
        return self.exchange_connector.fetch_open_orders(symbol=self.exchange_pair)
