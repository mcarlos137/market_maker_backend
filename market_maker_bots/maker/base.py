import time
from threading import Thread, Event
import random
import asyncio
import logging
import psycopg2
import os
import sys
sys.path.append(os.getcwd())
from damexCommons.base import OrderStatus, Order, OrderType, OrderSide, TradeSide
from damexCommons.connectors.base import ExchangeCommons
from damexCommons.businesses.base import SimpleBusiness
from damexCommons.tools.dbs import get_bot_db
from damexCommons.tools.damex_http_client import get_main_price

class MakerBotBase:
    
    def __init__(self, 
                bot_id: str,
                bot_type: str,
                active: bool,
                commons: dict[str, ExchangeCommons],
                exchange: str, 
                base_asset: str,
                quote_asset: str,
                tick_time: int,
                ) -> None:
                        
        self.bot_id = bot_id
        self.bot_type = bot_type
        self.active = active 
        self.commons = commons
        self.exchange = exchange
        self.base_asset = base_asset
        self.quote_asset = quote_asset
        self.tick_time = tick_time
        
        
class MakerBot(SimpleBusiness):
    
    def __init__(self, maker_bot_base: MakerBotBase) -> None:
        super().__init__(
            bot_id=maker_bot_base.bot_id,
            bot_type=maker_bot_base.bot_type,
            active=maker_bot_base.active,
            bot_db=get_bot_db(db_connection='bot', bot_type='maker'),
            commons=maker_bot_base.commons,
            exchange=maker_bot_base.exchange, 
            base_asset=maker_bot_base.base_asset,
            quote_asset=maker_bot_base.quote_asset,
            tick_time=maker_bot_base.tick_time,
            )
                    
        self.order_refresh_timestamp = {OrderSide.ASK.name: None, OrderSide.BID.name: None}
        
        self.orders_to_create: dict[str, list[Order]] = {OrderSide.ASK.name: [], OrderSide.BID.name: []}
            
        self.stop_check_threads['order_book'] = False    
                                        
        self.order_spread = 0
        self.order_amount = 0
        self.order_total_amount = 0
                                 
                             
    async def start(self) -> None:
        balance = await self.execute(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, name='fetch_balance', attributes=())
        self.balance_1h_start = {self.base_asset: float(balance[self.base_asset]['total']), self.quote_asset: float(balance[self.quote_asset]['total'])}
        self.balance_1h_timestamp = int(time.time() * 1e3)
        await self.refresh_strategy_and_target()
        await self.refresh_orders(sides=self.order_sides)
        t_1 = Thread(target=self.strategy_check_thread, args=(Event(),))
        t_1.start()   
        t_2 = Thread(target=self.orders_check_thread, args=(Event(),))
        t_2.start()                         
        t_3 = Thread(target=self.order_book_check_thread, args=(Event(),))
        t_3.start()
        t_4 = Thread(target=self.balance_1h_check_thread, args=(Event(),))
        t_4.start()
        t_5 = Thread(target=self.target_check_thread, args=(Event(),))
        t_5.start()
        if not self.started:
            self.started = True
    
    ####### custom threads                    
    def strategy_check_thread(self, event: Event) -> None:
        while True:
            if self.stop_check_threads['strategy']:
                logging.info('STOPPING strategy check thread============== %s', self.strategy["id"])
                self.stop_check_threads['strategy'] = False
                event.set()
                break            
            try:                
                logging.info('========== START strategy check thread ========== %s', self.strategy["id"]) 
                new_main_price = asyncio.run(get_main_price(base_asset=self.base_asset, quote_asset=self.quote_asset, price_decimals=self.commons[self.exchange + '__' + self.pair].price_decimals))
                main_price_movement = abs(self.main_price - new_main_price) * 100 / self.main_price
                logging.info('main price movement %s %s %s', main_price_movement, self.main_price, new_main_price)
                
                first_order_refresh_timestamp = 0
                if OrderSide.ASK.name in self.order_refresh_timestamp:
                    first_order_refresh_timestamp = self.order_refresh_timestamp[OrderSide.ASK.name]
                if OrderSide.BID.name in self.order_refresh_timestamp:
                    if first_order_refresh_timestamp == 0:
                        first_order_refresh_timestamp = self.order_refresh_timestamp[OrderSide.BID.name]
                    elif self.order_refresh_timestamp[OrderSide.BID.name] < first_order_refresh_timestamp:
                        first_order_refresh_timestamp = self.order_refresh_timestamp[OrderSide.BID.name]
                if (main_price_movement > self.strategy['order_price_refresh_tolerance_pct_uptrend'] and first_order_refresh_timestamp < (int(time.time() * 1e3) - (self.strategy['order_refresh_time_uptrend'] * 1e3))) or (main_price_movement < 0 and main_price_movement < self.strategy['order_price_refresh_tolerance_pct_downtrend'] and first_order_refresh_timestamp < (int(time.time() * 1e3) - (self.strategy['order_refresh_time_downtrend'] * 1e3))):
                    logging.info('CASE 1 - main price movement')
                    asyncio.run(self.refresh_orders(sides=self.order_sides))
                    continue       
                                
                for side in self.order_sides:
                    if self.order_refresh_timestamp[side] is not None and self.order_refresh_timestamp[side] < (int(time.time() * 1e3) - (self.strategy['max_order_age'] * 1e3)):
                        logging.info('CASE 2 - max order age')
                        asyncio.run(self.refresh_orders(sides=[side]))
                    elif self.strategy['order_refresh_level_min'][side] >= 0 and len(self.active_orders[side]) < self.strategy['order_refresh_level_min'][side]:
                        logging.info('CASE 3 - refresh level min')
                        asyncio.run(self.refresh_orders(sides=[side]))                

                logging.info('active BID orders len %s', len(self.active_orders["BID"]))    
                logging.info('active ASK orders len %s', len(self.active_orders["ASK"]))    
                    
                logging.info('========== FINISH strategy check thread ========== %s', self.strategy["id"]) 
                
                time.sleep(self.tick_time)
            except psycopg2.Error as e:
                logging.error('strategy check thread %s', e)
                time.sleep(1)
            except Exception as e:
                logging.error('strategy check thread %s', e)
                time.sleep(1)

    def order_book_check_thread(self, event: Event) -> None:
        while True:
            if self.stop_check_threads['order_book']:
                logging.info('STOPPING order book check thread==============')
                self.stop_check_threads['order_book'] = False
                event.set()
                break
            try:
                logging.info('========== START order book check thread ==========')
                order_book = asyncio.run(self.execute(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, name='fetch_order_book', attributes=()))
                if len(order_book['asks']) > 0 and len(order_book['bids']) > 0:
                    first_ask_order_price = float(order_book['asks'][0][0])
                    first_bid_order_price = float(order_book['bids'][0][0])
                    logging.info('first ASK order price %s', str(first_ask_order_price))
                    logging.info('first BID order price %s', str(first_bid_order_price))
                    for side in self.order_sides:
                        for active_order in self.active_orders[side]:
                            match side:
                                case OrderSide.BID.name:
                                    if first_ask_order_price <= active_order.price:
                                        asyncio.run(self.cancel_order(order=active_order))
                                case OrderSide.ASK.name:
                                    if first_bid_order_price >= active_order.price:
                                        asyncio.run(self.cancel_order(order=active_order))
                                        
                logging.info('========== FINISH order book check thread ==========')             
                time.sleep(self.tick_time)
            except Exception as e:
                logging.error('order_book_check thread %s', e)
                time.sleep(1)
           
      
    ####### custom methods                                                      
    async def refresh_orders(self, sides: list[str]) -> None:
        try:
            self.main_price = await get_main_price(base_asset=self.base_asset, quote_asset=self.quote_asset, price_decimals=self.commons[self.exchange + '__' + self.pair].price_decimals)
            for side in sides:
                logging.info('cancelling %s orders %s', side, len(self.active_orders[side]))
                await self.cancel_all_orders(side=side)
            balance = await self.execute(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, name='fetch_balance', attributes=())
            available_base_amount = float(balance[self.base_asset]['available'])
            available_quote_amount = float(balance[self.quote_asset]['available'])
            total_base_amount = float(balance[self.base_asset]['total'])
            total_quote_amount = float(balance[self.quote_asset]['total'])
            order_book = await self.execute(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, name='fetch_order_book', attributes=())
            self.orders_to_create[OrderSide.ASK.name] = []
            self.orders_to_create[OrderSide.BID.name] = []
            for side in sides:
                self.order_spread = 0
                self.order_amount = 0
                self.order_total_amount = 0
                self.order_refresh_timestamp[side] = int(time.time() * 1e3)
                i = 0
                self.order_spread = self.strategy['spread'][side]
                self.order_amount = round(self.strategy['order_amount'][side], self.commons[self.exchange + '__' + self.pair].base_amount_decimals)  
                self.order_total_amount = self.order_amount
                while i < self.strategy['order_levels'][side]:
                    i += 1    
                    price = (self.main_price - (self.main_price * self.order_spread / 100)) if side == OrderSide.BID.name else (self.main_price + (self.main_price * self.order_spread / 100))
                    price = round(price, self.commons[self.exchange + '__' + self.pair].price_decimals)
                    self.add_order(price=price, amount=self.order_amount, side=side)
                    match side:
                        case OrderSide.BID.name:
                            # BALANCE
                            if self.order_total_amount * price > available_quote_amount:
                                self.order_amount = (available_quote_amount / price) - (self.order_total_amount - self.order_amount)
                                self.orders_to_create[OrderSide.BID.name].pop()
                                if self.order_amount * price > self.commons[self.exchange + '__' + self.pair].quote_min_amount:
                                    self.add_order(price=price, amount=self.order_amount, side=side)
                                break
                            # TARGET
                            if self.target is not None and self.target['asset'] == self.base_asset and self.target['operation'] == TradeSide.BUY.name:
                                base_asset_diff = total_base_amount - self.target['initial_asset_amount']
                                if base_asset_diff + self.order_total_amount > self.target['operation_amount']:
                                    self.order_amount = self.target['operation_amount'] - (base_asset_diff + (self.order_total_amount - self.order_amount))
                                    self.orders_to_create[OrderSide.BID.name].pop()
                                    if self.order_amount * price > self.commons[self.exchange + '__' + self.pair].quote_min_amount:
                                        self.add_order(price=price, amount=self.order_amount, side=side)
                                    break
                            # 1h TRADE LIMIT
                            quote_asset_diff = total_quote_amount - self.balance_1h_start[self.quote_asset]
                            if (quote_asset_diff / price) + self.order_total_amount > self.strategy['trade_amount_limit_1h'][TradeSide.BUY.name]:
                                self.order_amount = self.strategy['trade_amount_limit_1h'][TradeSide.BUY.name] - ((quote_asset_diff / price) + (self.order_total_amount - self.order_amount))
                                self.orders_to_create[OrderSide.BID.name].pop()
                                if self.order_amount * price > self.commons[self.exchange + '__' + self.pair].quote_min_amount:
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
                                if self.order_amount > self.commons[self.exchange + '__' + self.pair].base_min_amount:
                                    self.add_order(price=price, amount=self.order_amount, side=side)
                                break
                            # TARGET
                            if self.target is not None and self.target['asset'] == self.base_asset and self.target['operation'] == TradeSide.SELL.name:
                                base_asset_diff = self.target['initial_asset_amount'] - total_base_amount
                                if base_asset_diff + self.order_total_amount > self.target['operation_amount']:
                                    self.order_amount = self.target['operation_amount'] - (base_asset_diff + (self.order_total_amount - self.order_amount))
                                    print('-----------------------2', self.order_total_amount, self.order_amount, base_asset_diff)
                                    self.orders_to_create[OrderSide.ASK.name].pop()
                                    if self.order_amount > self.commons[self.exchange + '__' + self.pair].base_min_amount:
                                        self.add_order(price=price, amount=self.order_amount, side=side)
                                    break
                                else:
                                    print('-----------------------1', self.order_total_amount, self.order_amount, base_asset_diff)
                            # 1h TRADE LIMIT
                            base_asset_diff = self.balance_1h_start[self.base_asset] - total_base_amount
                            if base_asset_diff + self.order_total_amount > self.strategy['trade_amount_limit_1h'][TradeSide.SELL.name]:
                                self.order_amount = self.strategy['trade_amount_limit_1h'][TradeSide.SELL.name] + (base_asset_diff + (self.order_total_amount - self.order_amount))
                                self.orders_to_create[OrderSide.ASK.name].pop()
                                if self.order_amount > self.commons[self.exchange + '__' + self.pair].base_min_amount:
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
                    await self.create_order(order=order_to_create)
        except Exception as e:
            logging.error('refresh orders %s', e)
        
        
    def increment_side_levels_value(self, side: str, add_to_order_total_amount: bool):
        self.order_spread += self.strategy['order_level_spread'][side]
        if add_to_order_total_amount:
            self.order_amount += round(self.strategy['order_level_amount'][side], self.commons[self.exchange + '__' + self.pair].base_amount_decimals)
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