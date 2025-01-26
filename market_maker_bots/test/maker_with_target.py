import time
import random
import logging
from logging.handlers import RotatingFileHandler
from damexCommons.base import OrderStatus, Order, OrderType, OrderSide, TradeSide


class MakerWithTarget:
    
    def __init__(self, 
                 bot_id: str, 
                 exchange: str, 
                 base_asset: str, 
                 quote_asset: str,
                 main_price: float
                ) -> None:
        self.bot_id = bot_id
        self.exchange = exchange
        self.base_asset = base_asset
        self.quote_asset = quote_asset
        self.main_price = main_price
        
        self.order_amount = 0
        self.order_total_amount = 0
        self.order_spread = 0
        
        self.pair = base_asset + '-' + quote_asset
        
        self.balance = {
            'HOT': {'available': 6000001.01834339, 'total': 6000001.01834339},
            'USDT': {'available': 100000, 'total': 100000},
        }

        self.strategy = {
            'id': 'test',
            'spread': {'ASK': 0.01, 'BID': 0.01},
            'order_amount': {'ASK': 1000000, 'BID': 1000000},
            'order_levels': {'ASK': 10, 'BID': 0},
            'trade_amount_limit_1h': {'SELL': 200000000, 'BUY': 200000000},
            'order_level_spread': {'ASK': 0.1, 'BID': 0.1},
            'order_level_amount': {'ASK': 0, 'BID': 0},
        }

        self.order_refresh_timestamp = {
            'ASK': None,
            'BID': None
        }

        self.target = {
            'asset': 'HOT',
            'operation': 'SELL',
            'initial_asset_amount': 6000001.01834339,
            'operation_amount': 5000000
        }

        self.balance_1h_start = {
            'HOT': 6000001.01834339,
            'USDT': 100000
        }
        
        self.commons = {
            'bitmart__HOT-USDT': {
                'base_amount_decimals': 2,
                'quote_amount_decimals': 2,
                'price_decimals': 8,
                'base_min_amount': 1,
                'quote_min_amount': 0.01
            }
        }
              
        self.orders_to_create = {
            'ASK': [],
            'BID': []
        }      
                
        logging.basicConfig(
            level=logging.INFO, 
            handlers=[
                logging.StreamHandler()
            ],
            format="%(asctime)s %(levelname)s %(message)s"
        )

    def refresh_orders(self, sides: list[str]) -> None:
        try:
            self.orders_to_create['ASK'] = []
            self.orders_to_create['BID'] = []
            #self.main_price = await get_main_price(base_asset=self.base_asset, quote_asset=self.quote_asset, price_decimals=self.commons[self.exchange + '__' + self.pair].price_decimals)
            #for side in sides:
            #    logging.info('cancelling %s orders %s', side, len(self.active_orders[side]))
            #    await self.cancel_all_orders(side=side)
            #balance = await self.execute(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, name='fetch_balance', attributes=())
            balance = self.balance
            available_base_amount = float(balance[self.base_asset]['available'])
            available_quote_amount = float(balance[self.quote_asset]['available'])
            total_base_amount = float(balance[self.base_asset]['total'])
            total_quote_amount = float(balance[self.quote_asset]['total'])
            #order_book = await self.execute(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, name='fetch_order_book', attributes=())
            order_book = {'asks': [], 'bids': []}
            #orders_to_create: dict[str, list[Order]] = {OrderSide.ASK.name: [], OrderSide.BID.name: []}
            for side in sides:
                self.order_spread = 0
                self.order_amount = 0
                self.order_total_amount = 0
                self.order_refresh_timestamp[side] = int(time.time() * 1e3)
                i = 0
                self.order_spread = self.strategy['spread'][side]
                self.order_amount = round(self.strategy['order_amount'][side], self.commons[self.exchange + '__' + self.pair]['base_amount_decimals'])  
                self.order_total_amount = self.order_amount
                while i < self.strategy['order_levels'][side]:
                    i += 1    
                    price = (self.main_price - (self.main_price * self.order_spread / 100)) if side == OrderSide.BID.name else (self.main_price + (self.main_price * self.order_spread / 100))
                    price = round(price, self.commons[self.exchange + '__' + self.pair]['price_decimals'])                    
                    self.add_order(price=price, amount=self.order_amount, side=side)
                    match side:
                        case OrderSide.BID.name:
                            # BALANCE
                            if self.order_total_amount * price > available_quote_amount:
                                self.order_amount = (available_quote_amount / price) - (self.order_total_amount - self.order_amount)
                                self.orders_to_create[OrderSide.BID.name].pop()
                                if self.order_amount * price > self.commons[self.exchange + '__' + self.pair]['quote_min_amount']:
                                    self.add_order(price=price, amount=self.order_amount, side=side)
                                break
                            # TARGET
                            if self.target is not None and self.target['asset'] == self.base_asset and self.target['operation'] == TradeSide.BUY.name:
                                base_asset_diff = total_base_amount - self.target['initial_asset_amount']
                                if base_asset_diff + self.order_total_amount > self.target['operation_amount']:
                                    self.order_amount = self.target['operation_amount'] - (base_asset_diff + (self.order_total_amount - self.order_amount))
                                    self.orders_to_create[OrderSide.BID.name].pop()
                                    if self.order_amount * price > self.commons[self.exchange + '__' + self.pair]['quote_min_amount']:
                                        self.add_order(price=price, amount=self.order_amount, side=side)
                                    break
                            # 1h TRADE LIMIT
                            quote_asset_diff = total_quote_amount - self.balance_1h_start[self.quote_asset]
                            if (quote_asset_diff / price) + self.order_total_amount > self.strategy['trade_amount_limit_1h'][TradeSide.BUY.name]:
                                print('-----', (quote_asset_diff / price), self.order_total_amount, self.strategy['trade_amount_limit_1h'][TradeSide.BUY.name])
                                self.order_amount = self.strategy['trade_amount_limit_1h'][TradeSide.BUY.name] - ((quote_asset_diff / price) + (self.order_total_amount - self.order_amount))
                                self.orders_to_create[OrderSide.BID.name].pop()
                                if self.order_amount * price > self.commons[self.exchange + '__' + self.pair]['quote_min_amount']:
                                    self.add_order(price=price, amount=self.order_amount, side=side)
                                break
                            # ORDER BOOK LEVEL
                            if len(order_book['asks']) > 0 and float(order_book['asks'][0][0]) <= price:
                                excluded_order = self.orders_to_create[side].pop()
                                logging.info('excluding order %s by order book level', excluded_order)
                                self.increment_side_levels_value(side=side, add_to_order_total_amount=False)
                                continue
                        case OrderSide.ASK.name:
                            # BALANCE
                            if self.order_total_amount > available_base_amount:
                                self.order_amount = available_base_amount - (self.order_total_amount - self.order_amount)
                                self.orders_to_create[OrderSide.ASK.name].pop()
                                if self.order_amount > self.commons[self.exchange + '__' + self.pair]['base_min_amount']:
                                    self.add_order(price=price, amount=self.order_amount, side=side)
                                break
                            # TARGET
                            if self.target is not None and self.target['asset'] == self.base_asset and self.target['operation'] == TradeSide.SELL.name:
                                base_asset_diff = self.target['initial_asset_amount'] - total_base_amount
                                if base_asset_diff + self.order_total_amount > self.target['operation_amount']:
                                    self.order_amount = self.target['operation_amount'] - (base_asset_diff + (self.order_total_amount - self.order_amount))
                                    self.orders_to_create[OrderSide.ASK.name].pop()
                                    if self.order_amount > self.commons[self.exchange + '__' + self.pair]['base_min_amount']:
                                        self.add_order(price=price, amount=self.order_amount, side=side)
                                    break
                            # 1h TRADE LIMIT
                            base_asset_diff = self.balance_1h_start[self.base_asset] - total_base_amount
                            if base_asset_diff + self.order_total_amount > self.strategy['trade_amount_limit_1h'][TradeSide.SELL.name]:
                                self.order_amount = self.strategy['trade_amount_limit_1h'][TradeSide.SELL.name] + (base_asset_diff + (self.order_total_amount - self.order_amount))
                                self.orders_to_create[OrderSide.ASK.name].pop()
                                if self.order_amount > self.commons[self.exchange + '__' + self.pair]['base_min_amount']:
                                    self.add_order(price=price, amount=self.order_amount, side=side)
                                break
                            # ORDER BOOK LEVEL
                            if len(order_book['bids']) > 0 and float(order_book['bids'][0][0]) >= price:
                                excluded_order = self.orders_to_create[side].pop()
                                logging.info('excluding order %s by order book level', excluded_order)
                                self.increment_side_levels_value(side=side, add_to_order_total_amount=False)
                                continue
                                                        
                    # Adding next level values
                    self.increment_side_levels_value(side=side, add_to_order_total_amount=True)
                                                
            for side in sides:
                logging.info('creating %s %s orders', len(self.orders_to_create[side]), side)
                for order_to_create in self.orders_to_create[side]:
                    logging.info('order to create %s', order_to_create)
                    #await self.create_order(order=order_to_create)
        except Exception as e:
            logging.error('refresh orders %s', e)
            
            
    def increment_side_levels_value(self, side: str, add_to_order_total_amount: bool):
        self.order_spread += self.strategy['order_level_spread'][side]
        if add_to_order_total_amount:
            self.order_amount += round(self.strategy['order_level_amount'][side], self.commons[self.exchange + '__' + self.pair]['base_amount_decimals'])
            self.order_total_amount += self.order_amount
            
    def add_order(self, price: float, amount: float, side: str):
        timestamp = int(time.time() * 1e3)
        order_id = ''.join(random.choice('0123456789ABCDEF') for i in range(16))
        order_to_create = Order(
            id=order_id, 
            bot_id=self.bot_id, 
            strategy_id=self.strategy['id'], 
            base_asset=self.base_asset, 
            quote_asset=self.quote_asset,
            creation_timestamp=timestamp,
            type=OrderType.LIMIT,
            price=float(price),
            amount=float(amount),
            last_status=OrderStatus.PENDING_TO_CREATE,
            last_update_timestamp=int(time.time() * 1e3),
            side=OrderSide.from_str(side),
            exchange=self.exchange
        )       
        self.orders_to_create[side].append(order_to_create)
            
            
maker_with_target = MakerWithTarget(bot_id='1', exchange='bitmart', base_asset='HOT', quote_asset='USDT', main_price=0.0014)

maker_with_target.refresh_orders(['ASK', 'BID'])