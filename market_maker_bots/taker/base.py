import time
from threading import Thread, Event
import random
import asyncio
import logging
import os
import sys
sys.path.append(os.getcwd())
from damexCommons.base import OrderStatus, TradeSide, Order, OrderSide, OrderType
from damexCommons.connectors.base import ExchangeCommons
from damexCommons.businesses.base import SimpleBusiness
from damexCommons.tools.dbs import get_bot_db
from damexCommons.tools.damex_http_client import get_inventory_values

class TakerBotBase:
    
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
        

class TakerBot(SimpleBusiness):
    
    def __init__(self, taker_bot_base: TakerBotBase) -> None:
        super().__init__(
            bot_id=taker_bot_base.bot_id,
            bot_type=taker_bot_base.bot_type,
            active=taker_bot_base.active,
            bot_db=get_bot_db(db_connection='bot', bot_type='taker'),
            commons=taker_bot_base.commons,
            exchange=taker_bot_base.exchange, 
            base_asset=taker_bot_base.base_asset,
            quote_asset=taker_bot_base.quote_asset,
            tick_time=taker_bot_base.tick_time,
            )
                                                                                         
                
    async def start(self) -> None:
        balance = await self.execute(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, name='fetch_balance', attributes=())
        self.balance_1h_start = {self.base_asset: float(balance[self.base_asset]['total']), self.quote_asset: float(balance[self.quote_asset]['total'])}
        self.balance_1h_timestamp = int(time.time() * 1e3)
        await self.refresh_strategy_and_target()
        t_1 = Thread(target=self.strategy_check_thread, args=(Event(),))
        t_1.start()                            
        t_2 = Thread(target=self.orders_check_thread, args=(Event(),))
        t_2.start()
        t_3 = Thread(target=self.balance_1h_check_thread, args=(Event(),))
        t_3.start() 
        t_4 = Thread(target=self.target_check_thread, args=(Event(),))
        t_4.start() 
            
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
                order_book = asyncio.run(self.execute(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, name='fetch_order_book', attributes=())) 
                order_book_db = asyncio.run(self.exchange_db.get_order_book_db(base_asset=self.base_asset, quote_asset=self.quote_asset, size=3, exchange=self.exchange))
                                
                logging.info('order_book %s', order_book)
                logging.info('order_book_db %s', order_book_db)
                
                balance = asyncio.run(self.execute(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, name='fetch_balance', attributes=()))
                available_base_amount = float(balance[self.base_asset]['available'])
                available_quote_amount = float(balance[self.quote_asset]['available'])
                
                logging.info('balance %s', balance)
                                
                position = None
                vwap = None
                
                if self.strategy['use_vwap'] in ['EXCHANGE', 'GENERAL']:
                    inventory_values = asyncio.run(get_inventory_values(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset))
                    position = inventory_values['position']
                    vwap = inventory_values['vwap']
                    logging.info('inventory_values %s', inventory_values)
                    
                logging.info('position %s', position)
                logging.info('vwap %s', vwap)
                
                order_sides = None
                
                if self.strategy['execution_side_type'] == 'ONLY_BUY':
                    order_sides = [OrderSide.BID]
                elif self.strategy['execution_side_type'] == 'ONLY_SELL':
                    order_sides = [OrderSide.ASK]
                elif self.strategy['execution_side_type'] == 'BUY_OR_SELL':
                    order_sides = [OrderSide.BID, OrderSide.ASK]
                elif self.strategy['execution_side_type'] == 'SELL_OR_BUY':
                    order_sides = [OrderSide.ASK, OrderSide.BID]
                    
                logging.info('order_sides %s', order_sides)

                if position is not None and position < 0 and OrderSide.ASK in order_sides: 
                    order_sides.remove(OrderSide.ASK)
                
                if position is not None and position > 0 and OrderSide.BID in order_sides: 
                    order_sides.remove(OrderSide.BID)
                                                           
                for order_side in order_sides:
                    if order_side == OrderSide.ASK:
                        for order_book_bid in order_book['bids']:
                            price_bid = float(order_book_bid[0])
                            amount_bid = float(order_book_bid[1])    
                                                        
                            if amount_bid < self.strategy['min_order_amount']:
                                continue
                            
                            order_exist = asyncio.run(self.bot_db.order_by_strategy_side_price_exist_db(order_side=OrderSide.ASK, price=price_bid, exchange=self.exchange))
                            if order_exist: 
                                logging.info('ASK order already exist %s', price_bid)
                                continue
                            
                            if vwap is not None and price_bid * self.strategy['vwap_price_factor'] >= vwap:
                                continue
                            
                            if self.strategy['only_price_opportunities'] and len(order_book_db['bids']) < 1:
                                continue
                            
                            if self.strategy['only_price_opportunities'] and price_bid <= order_book_db['bids'][0][0]:
                                continue
                            
                            if not self.strategy['only_price_opportunities'] and self.strategy['limit_price'] == 0:
                                continue
                            
                            if price_bid <= self.strategy['limit_price']:
                                continue
                            
                            if float(amount_bid) > float(self.strategy['max_order_amount']):
                                amount_bid = self.strategy['max_order_amount']
                                                        
                            # Checking target                            
                            if self.target is not None and self.target['asset'] == self.base_asset and self.target['operation'] == TradeSide.SELL.name:
                                base_asset_diff = self.target['initial_asset_amount'] - available_base_amount
                                if base_asset_diff >= self.target['operation_amount']:
                                    logging.info('excluding order because target reached')
                                    continue
                                elif amount_bid > self.target['operation_amount'] - base_asset_diff:
                                    amount_bid = self.target['operation_amount'] - base_asset_diff
                            
                            # Checking 1h trade limit                                                  
                            base_asset_diff = self.balance_1h_start[self.base_asset] - available_base_amount
                            if base_asset_diff >= self.strategy['trade_amount_limit_1h'][TradeSide.SELL.name]:
                                logging.info('excluding order by 1h trade limit')
                                continue
                            elif amount_bid > self.strategy['trade_amount_limit_1h'][TradeSide.SELL.name] - base_asset_diff:
                                amount_bid = self.strategy['trade_amount_limit_1h'][TradeSide.SELL.name] - base_asset_diff                                
                            
                            # Checking minimum available base amount              
                            if self.commons[self.exchange + '__' + self.pair].base_min_amount >= available_base_amount:
                                logging.info('excluding order by minimum available base amount')
                                continue
                            
                            # Checking minimum order amount              
                            if amount_bid < self.commons[self.exchange + '__' + self.pair].base_min_amount:
                                logging.info('excluding order by minimum order amount')
                                continue
                                                        
                            timestamp = int(time.time() * 1e3)
                            order_to_create: Order = Order(
                                id=''.join(random.choice('0123456789ABCDEF') for i in range(16)), 
                                bot_id=self.bot_id, 
                                strategy_id=self.strategy['id'], 
                                base_asset=self.base_asset, 
                                quote_asset=self.quote_asset,
                                creation_timestamp=timestamp,
                                type=OrderType.LIMIT,
                                price=float(price_bid),
                                amount=float(amount_bid),
                                last_status=OrderStatus.PENDING_TO_CREATE,
                                last_update_timestamp=timestamp,
                                side=OrderSide.ASK,
                                exchange=self.exchange
                            )
                            asyncio.run(self.create_order(order=order_to_create))
                            logging.info('creating order %s', order_to_create)
                            break

                    if order_side is OrderSide.BID:
                        for order_book_ask in order_book['asks']:
                            price_ask = float(order_book_ask[0])
                            amount_ask = float(order_book_ask[1])
                            
                            if amount_ask < self.strategy['min_order_amount']:
                                continue
                            
                            order_exist = asyncio.run(self.bot_db.order_by_strategy_side_price_exist_db(order_side=OrderSide.BID, price=price_ask, exchange=self.exchange))
                            if order_exist: 
                                logging.info('BID order already exist %s', price_bid)
                                continue
                            
                            if vwap is not None and price_ask * self.strategy['vwap_price_factor'] < vwap:
                                continue
                            
                            if self.strategy['only_price_opportunities'] and len(order_book_db['asks']) < 1:
                                continue
                            
                            if self.strategy['only_price_opportunities'] and price_ask >= order_book_db['asks'][0][0]:
                                continue
                            
                            if not self.strategy['only_price_opportunities'] and self.strategy['limit_price'] == 0:
                                continue
                            
                            if price_ask >= self.strategy['limit_price']:
                                continue
                            
                            if float(amount_ask) > float(self.strategy['max_order_amount']):
                                amount_ask = self.strategy['max_order_amount']
                                
                            # Checking target
                            if self.target is not None and self.target['asset'] == self.base_asset and self.target['operation'] == TradeSide.BUY.name:
                                base_asset_diff = available_base_amount - self.target['initial_asset_amount']
                                if base_asset_diff >= self.target['operation_amount']:
                                    logging.info('excluding order because target reached')
                                    continue
                                elif amount_ask > self.target['operation_amount'] - base_asset_diff:
                                    amount_ask = self.target['operation_amount'] - base_asset_diff
                            
                            # Checking 1h trade limit                                    
                            base_asset_diff = available_base_amount - self.balance_1h_start[self.quote_asset]
                            if base_asset_diff >= self.strategy['trade_amount_limit_1h'][TradeSide.BUY.name]:
                                logging.info('excluding order by 1h trade limit')
                                continue
                            elif amount_ask > self.strategy['trade_amount_limit_1h'][TradeSide.BUY.name] - base_asset_diff:
                                amount_ask = self.strategy['trade_amount_limit_1h'][TradeSide.BUY.name] - base_asset_diff 
                            
                            # Checking minimum available      
                            if self.commons[self.exchange + '__' + self.pair].quote_min_amount >= available_quote_amount:
                                logging.info('excluding order by minimum available quote amount')
                                continue    

                            # Checking minimum order amount              
                            if amount_ask * self.main_price < self.commons[self.exchange + '__' + self.pair].quote_min_amount:
                                logging.info('excluding order by minimum order amount')
                                continue
                                
                            timestamp = int(time.time() * 1e3)
                            order_to_create: Order = Order(
                                id=''.join(random.choice('0123456789ABCDEF') for i in range(16)), 
                                bot_id=self.bot_id, 
                                strategy_id=self.strategy['id'], 
                                base_asset=self.base_asset, 
                                quote_asset=self.quote_asset,
                                creation_timestamp=timestamp,
                                type=OrderType.LIMIT,
                                price=float(price_ask),
                                amount=float(amount_ask),
                                last_status=OrderStatus.PENDING_TO_CREATE,
                                last_update_timestamp=timestamp,
                                side=OrderSide.BID,
                                exchange=self.exchange
                            )
                            asyncio.run(self.create_order(order=order_to_create))
                            logging.info('creating order %s', order_to_create)    
                            break
                            
                logging.info('========== FINISH strategy check thread ========== %s', self.strategy["id"]) 
                
                time.sleep(self.tick_time)
            except Exception as e:
                logging.error('strategy check thread %s', e)
                time.sleep(1)
                                                             