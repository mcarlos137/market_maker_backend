import time
from threading import Thread, Event
import random
import asyncio
import logging
import os
import sys
sys.path.append(os.getcwd())
from damexCommons.base import OrderStatus, Order, OrderSide, OrderType, TradeSide
from damexCommons.connectors.base import ExchangeCommons
from damexCommons.tools.dbs import get_bot_db
from damexCommons.businesses.base import SimpleBusiness
from damexCommons.tools.utils import DIFF_BUY_SELL_LIMIT_TO_INACTIVATE_VOL_BOT, MIN_BALANCE_TO_INACTIVATE_VOL_BOT
from damexCommons.tools.damex_http_client import get_main_price

class VolBotBase:
    
    def __init__(self, 
                bot_id: str,
                bot_type: str,
                active: bool,
                commons: dict[str, ExchangeCommons],
                exchange: str,
                base_asset: str,
                quote_asset: str,
                tick_time: int,
                ):
        
        self.bot_id = bot_id
        self.bot_type = bot_type
        self.active = active
        self.commons = commons
        self.exchange = exchange
        self.base_asset = base_asset
        self.quote_asset = quote_asset
        self.tick_time=tick_time
        
        
class VolBot(SimpleBusiness):
    
    def __init__(self, vol_bot_base: VolBotBase) -> None:
        super().__init__(
            bot_id=vol_bot_base.bot_id,
            bot_type=vol_bot_base.bot_type,
            active=vol_bot_base.active,
            bot_db=get_bot_db(db_connection='bot', bot_type='vol'),
            commons=vol_bot_base.commons,
            exchange=vol_bot_base.exchange, 
            base_asset=vol_bot_base.base_asset,
            quote_asset=vol_bot_base.quote_asset,
            tick_time=vol_bot_base.tick_time,
            )

        self.stop_check_threads['inactivate'] = False

        self.current_amount = 0
        self.app_last_trade_timestamp = None  
        self.out_of_range_price_timestamp = None
        self.continuous_errors_count = 0
        self.trade_1h_timestamp = None
                         
                                         
    async def start(self) -> None:
        await self.refresh_strategy_and_target()
        t_1 = Thread(target=self.strategy_check_thread, args=(Event(),))
        t_1.start()                            
        t_2 = Thread(target=self.orders_check_thread, args=(Event(),))
        t_2.start()
        t_3 = Thread(target=self.inactivate_check_thread, args=(Event(),))
        t_3.start()
        if not self.started:
            self.started = True

    def strategy_check_thread(self, event: Event) -> None:
        while True:
            if self.stop_check_threads['strategy']:
                logging.info('STOPPING strategy check thread==============')
                self.stop_check_threads['strategy'] = False
                event.set()
                break   
            try:
                logging.info('========== START strategy check thread ==========')    
                if self.current_amount <= self.strategy['target_amount']:
                    order_book = asyncio.run(self.execute(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, name='fetch_order_book', attributes=())) 
                    logging.info('order_book %s', order_book)
                    amount = round(random.uniform(self.strategy['lower_order_amount'], self.strategy['higher_order_amount']), self.commons[self.exchange + '__' + self.pair].base_amount_decimals)
                    price = asyncio.run(get_main_price(base_asset=self.base_asset, quote_asset=self.quote_asset, price_decimals=self.commons[self.exchange + '__' + self.pair].price_decimals)) + round(random.uniform(-self.strategy['price_band'], self.strategy['price_band']), self.commons[self.exchange + '__' + self.pair].price_decimals)
                    logging.info('price 1 -> %s', price)
                    highest_bid = float(order_book['bids'][0][0])
                    lowest_ask = float(order_book['asks'][0][0])
                    logging.info('highest bid %s', highest_bid)
                    logging.info('lowest ask %s', lowest_ask)
                    order_book_spread = float(lowest_ask) - float(highest_bid)
                    if order_book_spread < 0.00020:
                        logging.info('spread is too low to send vol trades %s', order_book_spread)
                        time.sleep(5)
                        continue
                    
                    main_price_parameters = asyncio.run(self.exchange_db.get_main_price_parameters_db(base_asset=self.base_asset, quote_asset=self.quote_asset))
                    out_of_range_price = False
                    if not (price < lowest_ask and price > highest_bid):
                        if main_price_parameters['price_floor'] > highest_bid:
                            price = round(lowest_ask - self.strategy['price_band'], self.commons[self.exchange + '__' + self.pair].price_decimals)
                            out_of_range_price = True
                        if main_price_parameters['price_ceiling'] < lowest_ask:
                            price = round(highest_bid + self.strategy['price_band'], self.commons[self.exchange + '__' + self.pair].price_decimals)
                            out_of_range_price = True                        
                    if out_of_range_price:
                        if self.out_of_range_price_timestamp is None:
                            self.out_of_range_price_timestamp = int(time.time() * 1e3)
                        if not self.strategy['floating_price']:
                            time.sleep(30)
                            continue
                    else:
                        self.out_of_range_price_timestamp = None
                    
                    filled_amount = amount * price
                    self.current_amount += filled_amount
                    
                    first_order_side = OrderSide.BID if random.randint(0, 1) else OrderSide.ASK
                    first_order_aux = False
                       
                    if self.exchange_aux + '__' + self.pair in self.commons:
                        balance_aux = asyncio.run(self.execute(exchange=self.exchange_aux, base_asset=self.base_asset, quote_asset=self.quote_asset, name='fetch_balance', attributes=()))
                        available_base_amount_aux = float(balance_aux[self.base_asset]['available'])
                        available_quote_amount_aux = float(balance_aux[self.quote_asset]['available'])
                        first_order_aux = True if random.randint(0, 1) == 1 else False
                        if first_order_aux:
                            if available_base_amount_aux >= 1000 and available_quote_amount_aux < 100:
                                first_order_side = OrderSide.ASK
                            elif available_base_amount_aux < 1000 and available_quote_amount_aux >= 100:
                                first_order_side = OrderSide.BID
                    
                    second_order_side = OrderSide.ASK if first_order_side == OrderSide.BID else OrderSide.BID
                    second_order_aux = not first_order_aux and self.exchange_aux + '__' + self.pair in self.commons
                    
                    timestamp = int(time.time() * 1e3)    
                    id_1 = ''.join(random.choice('0123456789ABCDEF') for i in range(16))
                    order_1 = Order(
                        id=id_1, 
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
                        side=first_order_side,
                        exchange=self.exchange,
                        aux=first_order_aux
                    )    
                    asyncio.run(self.create_order(order=order_1))
                    logging.info('creating order 1 -> %s', order_1)
                    time.sleep(1)
                    id_2 = ''.join(random.choice('0123456789ABCDEF') for i in range(16))
                    order_2 = Order(
                        id=id_2, 
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
                        side=second_order_side,
                        exchange=self.exchange,
                        aux=second_order_aux
                    )
                    asyncio.run(self.create_order(order=order_2))
                    logging.info('creating order 2 -> %s', order_2)
                    upper_limit_time = int((86400 * 2 / (self.strategy['target_amount'] / (price * (self.strategy['lower_order_amount'] + self.strategy['higher_order_amount']) / 2))) - self.strategy['lower_order_time'])
                    logging.info('upper_limit_time %s', upper_limit_time)
                    logging.info('Current = %s', self.current_amount)
                    logging.info('24h estimation = %s', (86400 * self.current_amount) / int((int(time.time() * 1000) - self.initial_timestamp) / 1000))
                    time.sleep(random.randint(self.strategy['lower_order_time'], upper_limit_time)) 
                else:
                    final_time = int(time.time() * 1000)
                    logging.info('Seconds to get the target = %s', (final_time - self.initial_timestamp) / 1000)
                    self.current_amount = 0
                    self.initial_timestamp = final_time
                    time.sleep(60)
                self.continuous_errors_count = 0
                logging.info('========== FINISH strategy check thread ==========')          
            except Exception as e:
                logging.error('strategy check thread %s', e)
                self.continuous_errors_count += 1
                time.sleep(random.randint(30, 60))
                
                                            
    def inactivate_check_thread(self, event: Event) -> None:
        while True:
            if self.stop_check_threads['inactivate']:
                logging.info('STOPPING inactivate check thread==============')
                self.stop_check_threads['inactivate'] = False
                event.set()
                break
            try:
                inactivate = False
                inactivation_reason = ''
                balance = asyncio.run(self.execute(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, name='fetch_balance', attributes=()))
                total_base_amount = float(balance[self.base_asset]['total'])
                total_quote_amount = float(balance[self.quote_asset]['total'])
                if (self.exchange_aux + '__' + self.pair) in self.commons: 
                    balance_aux = asyncio.run(self.execute(exchange=self.exchange_aux, base_asset=self.base_asset, quote_asset=self.quote_asset, name='fetch_balance', attributes=()))
                    total_base_amount_aux = float(balance_aux[self.base_asset]['total'])
                    total_quote_amount_aux = float(balance_aux[self.quote_asset]['total'])
                    if (total_base_amount < MIN_BALANCE_TO_INACTIVATE_VOL_BOT[self.base_asset] and total_base_amount_aux < MIN_BALANCE_TO_INACTIVATE_VOL_BOT[self.base_asset]) or (total_quote_amount < MIN_BALANCE_TO_INACTIVATE_VOL_BOT[self.quote_asset] and total_quote_amount_aux < MIN_BALANCE_TO_INACTIVATE_VOL_BOT[self.quote_asset]):
                        inactivate = True
                        inactivation_reason = 'bot account out of balance'
                else:
                    if total_base_amount < MIN_BALANCE_TO_INACTIVATE_VOL_BOT[self.base_asset] or total_quote_amount < MIN_BALANCE_TO_INACTIVATE_VOL_BOT[self.quote_asset]:
                        inactivate = True
                        inactivation_reason = 'bot account out of balance'
                if int(self.strategy['inactivation_threshold']) > 0:
                    if self.out_of_range_price_timestamp is not None and self.out_of_range_price_timestamp < (int(time.time() * 1e3) - (self.strategy['inactivation_threshold'] * 1e3)):
                        inactivate = True
                        inactivation_reason = 'market price out of range'
                if self.continuous_errors_count == 10:
                    inactivate = True
                    inactivation_reason = 'there are some errors in the execution'
                timestamp = int(time.time() * 1e3)
                if self.trade_1h_timestamp is None or timestamp - (60 * 60 * 1e3) > self.trade_1h_timestamp:
                    self.trade_1h_timestamp = timestamp
                buy_trades_sum_db = asyncio.run(self.exchange_db.get_trades_sum_db(
                    exchange=self.exchange, 
                    base_asset=self.base_asset,
                    quote_asset=self.quote_asset,
                    bot_type=self.bot_type,
                    trade_side=TradeSide.BUY,
                    timestamp=self.trade_1h_timestamp
                    ))
                    
                sell_trades_sum_db = asyncio.run(self.exchange_db.get_trades_sum_db(
                    exchange=self.exchange, 
                    base_asset=self.base_asset,
                    quote_asset=self.quote_asset,
                    bot_type=self.bot_type,
                    trade_side=TradeSide.SELL,
                    timestamp=self.trade_1h_timestamp
                    ))
                logging.info('diff trades buy - sell %s', buy_trades_sum_db - sell_trades_sum_db) 
                    
                if buy_trades_sum_db - sell_trades_sum_db > DIFF_BUY_SELL_LIMIT_TO_INACTIVATE_VOL_BOT[self.base_asset]:
                    inactivate = True
                    inactivation_reason = 'buy minus sell limit exceeded'
                if inactivate:
                    time.sleep(10)
                    asyncio.run(self.self_inactivate(reason=inactivation_reason))
                    self.out_of_range_price_timestamp = None
                    self.continuous_errors_count = 0
            except Exception as e:
                logging.error('inactivate_check thread %s', e)   
            time.sleep(5)

    async def refresh_orders(self, sides: list[str]) -> None:
        pass