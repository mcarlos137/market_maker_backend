import time
from threading import Thread, Event
import json
import pika
import asyncio
import logging
import random
from pathlib import Path
from typing import Optional
import os
import sys
import itertools
sys.path.append(os.getcwd())
from damexCommons.base import Trade, TradeSide, OrderType, OrderStatus, Order, OrderSide
from damexCommons.connectors.base import ExchangeCommons
from damexCommons.businesses.base import ComplexBusiness
from damexCommons.tools.dbs import get_bot_db
from damexCommons.tools.utils import send_alert
from damexCommons.tools.damex_http_client import fetch_emulated_balance_new, execute_emulated_balance_new


class ArbitrageBotBase:
    
    def __init__(self, 
                bot_id: str,
                bot_type: str,
                active: bool,
                commons: dict[str, ExchangeCommons],
                exchanges: list[str], 
                base_assets: list[str],
                quote_asset: str,
                testing: Optional[bool] = True,
                emulated_balance: Optional[str] = None
                ) -> None:
        
        self.bot_id = bot_id
        self.bot_type = bot_type
        self.active = active
        self.commons = commons
        self.exchanges = exchanges
        self.base_assets = base_assets
        self.quote_asset = quote_asset
        self.testing = testing
        self.emulated_balance = emulated_balance
        
        
class ArgitrageBot(ComplexBusiness):
    
    def __init__(self, arbitrage_bot_base: ArbitrageBotBase) -> None:
        super().__init__(
            bot_id=arbitrage_bot_base.bot_id,
            bot_type=arbitrage_bot_base.bot_type,
            active=arbitrage_bot_base.active,
            bot_db=get_bot_db(db_connection='bot', bot_type='arbitrage'),
            commons=arbitrage_bot_base.commons,
            exchanges=arbitrage_bot_base.exchanges, 
            base_assets=arbitrage_bot_base.base_assets,
            quote_asset=arbitrage_bot_base.quote_asset,
            )
        self.testing = arbitrage_bot_base.testing
        self.emulated_balance = arbitrage_bot_base.emulated_balance
        
        self.trade_time = None
        self.order_books = {}
        self.stop_ws = {}
                                            
    async def start(self) -> None:
        await self.refresh_strategy_and_target()
        if not self.testing:
            t_1 = Thread(target=self.orders_check_thread, args=(Event(),))
            t_1.start()       
        for exchange in self.exchanges:
            for base_asset in self.base_assets:
                thread_id = exchange + '__' + base_asset + '-' + self.quote_asset
                self.stop_check_threads[thread_id] = False
                thread = Thread(target=self.order_book_thread, args=(exchange, base_asset, self.quote_asset, Event(),))
                thread.start()
            
        if not self.started:
            self.started = True  
    
    def execution(self, ch, method, properties, body):
        body_json = json.loads(body)
        order_book_time = body_json['time']
        exchange = body_json['exchange']
        base_asset = body_json['base_asset']
        quote_asset = body_json['quote_asset']
        data = body_json['data']
        pair: str = base_asset + '-' + quote_asset   
        
        logging.info('incoming data from %s %s %s', order_book_time, exchange, pair)
        
        if pair not in self.order_books:
            self.order_books[pair] = {}     
        if data is not None and len(data) > 0:
            data['time'] = order_book_time
            self.order_books[pair][exchange] = data
          
        if len(self.order_books[pair]) == 1:
            return
                                
        exchange_groups = list(itertools.combinations(self.exchanges, 2))
        logging.info('exchange_groups %s', exchange_groups)
        for exchange_group in exchange_groups:
            exchange_combinations = [
                {'exchange_1': exchange_group[0], 'exchange_2': exchange_group[1]},
                {'exchange_1': exchange_group[1], 'exchange_2': exchange_group[0]}
            ]
            logging.info('exchange_combinations %s', exchange_combinations)                
            for exchange_combination in exchange_combinations:
                exchange_1 = exchange_combination['exchange_1']
                exchange_2 = exchange_combination['exchange_2']
                if exchange_1 not in self.order_books[pair] or len(self.order_books[pair][exchange_1]["asks"]) == 0 or self.order_books[pair][exchange_1]["time"] < int(time.time() * 1e3) - (60 * 1e3):
                    continue
                if exchange_2 not in self.order_books[pair] or len(self.order_books[pair][exchange_2]["bids"]) == 0 or self.order_books[pair][exchange_2]["time"] < int(time.time() * 1e3) - (60 * 1e3):
                    continue
                logging.info('comparing %s with %s in pair %s', exchange_1, exchange_2, pair)
                logging.info('first %s ASK %s', exchange_1, self.order_books[pair][exchange_1]["asks"][0])
                logging.info('first %s BID %s', exchange_2, self.order_books[pair][exchange_2]["bids"][0])
                
                if self.trade_time is not None and int(time.time() * 1e3) - (20 * 1000) < self.trade_time:
                    continue       
                bid_levels = 0
                total_bid_amount = 0
                bids_price_per_amount_sum = 0
                first_ask_price = float(self.order_books[pair][exchange_1]['asks'][0][0])
                for bid in self.order_books[pair][exchange_2]['bids']:
                    bid_price = float(bid[0])
                    bid_amount = float(bid[1])
                    if first_ask_price < bid_price:
                        bids_price_per_amount_sum += bid_price * bid_amount
                        total_bid_amount += bid_amount
                        if bids_price_per_amount_sum > DEPTHS[base_asset]['max']:
                            bids_price_per_amount_sum -= bid_price * bid_amount
                            total_bid_amount -= bid_amount
                            bids_price_per_amount_sum += bid_price * (DEPTHS[base_asset]['max'] - total_bid_amount)
                            total_bid_amount += (DEPTHS[base_asset]['max'] - total_bid_amount)
                        bid_levels += 1
                        if total_bid_amount >= DEPTHS[base_asset]['max']:
                            break
                    else:
                        break
                ask_levels = 0
                total_ask_amount = 0
                asks_price_per_amount_sum = 0
                first_bid_price = float(self.order_books[pair][exchange_2]['bids'][0][0])
                for ask in self.order_books[pair][exchange_1]['asks']:
                    ask_price = float(ask[0])
                    ask_amount = float(ask[1])
                    if first_bid_price > ask_price:
                        asks_price_per_amount_sum += ask_price * ask_amount
                        total_ask_amount += ask_amount
                        if asks_price_per_amount_sum > DEPTHS[base_asset]['max']:
                            asks_price_per_amount_sum -= ask_price * ask_amount
                            total_ask_amount -= ask_amount
                            asks_price_per_amount_sum += ask_price * (DEPTHS[base_asset]['max'] - total_ask_amount)
                            total_ask_amount += (DEPTHS[base_asset]['max'] - total_ask_amount)
                        ask_levels += 1
                        if total_ask_amount >= DEPTHS[base_asset]['max']:
                            break
                depth = total_bid_amount
                levels = bid_levels
                if total_ask_amount < depth:
                    depth = total_ask_amount
                    levels = ask_levels
                if levels != 1:
                    logging.info('-----------------------------------0 levels is not 1 %s', levels)
                    continue
                if depth < DEPTHS[base_asset]['min']:
                    logging.info('-----------------------------------1 min depth is not reached %s %s', depth, DEPTHS[base_asset]["min"])
                    continue
                ask_avg_price = asks_price_per_amount_sum / total_ask_amount
                bid_avg_price = bids_price_per_amount_sum / total_bid_amount
                arb_opportunity = bid_avg_price - ask_avg_price
                
                profitability = (arb_opportunity * 100 / ask_avg_price) - (self.commons[exchange_1 + '__' + base_asset + '-' + quote_asset].buy_fee_percentage + self.commons[exchange_2 + '__' + base_asset + '-' + quote_asset].sell_fee_percentage)
                if profitability < self.strategy['min_profitability']:
                    logging.info('-----------------------------------2 min profitability is not reached %s %s', profitability, self.strategy["min_profitability"])
                    continue
                balances = asyncio.run(self.fetch_balances(exchanges=[exchange_1, exchange_2], base_asset=base_asset))
                if balances[exchange_1][quote_asset]['available'] * 0.98 < depth * ask_avg_price:
                    logging.info('-----------------------------------3 not enough balance to buy in %s %s < %s', exchange_1, balances[exchange_1][quote_asset]["available"] * 0.98, ask_avg_price * ask_avg_price)
                    continue
                if balances[exchange_2][base_asset]['available'] * 0.98 < depth:
                    logging.info('-----------------------------------4 not enough balance to sell in %s %s < %s', exchange_2, balances[exchange_2][base_asset]["available"] * 0.98, depth)
                    continue
                                
                if not self.testing:
                    if self.trade_time is not None and int(time.time() * 1e3) - (20 * 1000) < self.trade_time:
                        continue
                    self.trade_time = int(time.time() * 1e3)            
                    logging.info('-------------------CREATING LIMIT ORDERS-------------------')
                        
                    order_id = ''.join(random.choice('0123456789ABCDEF') for i in range(16))
                    timestamp = int(time.time() * 1e3)
                    try:
                        order_1 = Order(
                            id=order_id, 
                            bot_id=self.bot_id, 
                            strategy_id=self.strategy['id'], 
                            base_asset=base_asset, 
                            quote_asset=self.quote_asset,
                            creation_timestamp=timestamp,
                            type=OrderType.LIMIT,
                            price=float(ask_avg_price),
                            amount=float(depth),
                            last_status=OrderStatus.PENDING_TO_CREATE,
                            last_update_timestamp=int(time.time() * 1e3),
                            side=OrderSide.BID,
                            exchange=exchange_1,
                        )
                        self.create_order(order=order_1)
                        order_2 = Order(
                            id=order_id, 
                            bot_id=self.bot_id, 
                            strategy_id=self.strategy['id'], 
                            base_asset=base_asset, 
                            quote_asset=self.quote_asset,
                            creation_timestamp=timestamp,
                            type=OrderType.LIMIT,
                            price=float(bid_avg_price),
                            amount=float(depth),
                            last_status=OrderStatus.PENDING_TO_CREATE,
                            last_update_timestamp=int(time.time() * 1e3),
                            side=OrderSide.ASK,
                            exchange=exchange_2,
                        )
                        self.create_order(order=order_2)
                    except Exception as e:
                        logging.error('------------------------------------------PROBLEM CREATING ARBITRAGE ORDERS %s', e)
                    continue
                        
                elif self.emulated_balance is not None:
                    if self.trade_time is not None and int(time.time() * 1e3) - (20 * 1e3) < self.trade_time:
                        continue
                    self.trade_time = int(time.time() * 1e3)
                              
                    logging.info('-------------------CREATING TRADES STARTS------------------- %s', self.trade_time)
                        
                    fee_buy = {"cost": depth * ask_avg_price * self.commons[exchange_1 + '__' + base_asset + '-' + quote_asset].buy_fee_percentage / 100, "currency": quote_asset}
                    if self.commons[exchange_1 + '__' + base_asset + '-' + quote_asset].buy_fee_asset_type == 'base':
                        fee_buy = {"cost": depth * self.commons[exchange_1 + '__' + base_asset + '-' + quote_asset].buy_fee_percentage / 100, "currency": base_asset}
                    fee_sell = {"cost": bid_avg_price * depth * self.commons[exchange_2 + '__' + base_asset + '-' + quote_asset].sell_fee_percentage / 100, "currency": "USDT"}
                        
                    trade_1 = Trade(bot_id=self.bot_id, strategy_id=self.strategy['id'], base_asset=base_asset, quote_asset=quote_asset, timestamp=self.trade_time, order_id='', side=TradeSide.BUY, price=float(ask_avg_price), amount=float(depth), fee=fee_buy, exchange_id='', exchange=exchange_1)
                    logging.info('-------------------trade_1------------------- %s', trade_1)    
                    asyncio.run(self.bot_db.create_trade_db(trade=trade_1))
                        
                    trade_2 = Trade(bot_id=self.bot_id, strategy_id=self.strategy['id'], base_asset=base_asset, quote_asset=quote_asset, timestamp=self.trade_time, order_id='', side=TradeSide.SELL, price=float(bid_avg_price), amount=float(depth), fee=fee_sell, exchange_id='', exchange=exchange_2)
                    logging.info('-------------------trade_2------------------- %s', trade_2)    
                    asyncio.run(self.bot_db.create_trade_db(trade=trade_2))
                        
                    #send_alert(alert_type='arbitrage_trades', message_values={}, channel='telegram_group_3')
                              
                    asyncio.run(execute_emulated_balance_new(
                        name=self.emulated_balance, 
                        exchange=exchange_1,
                        asset=quote_asset,
                        amount=ask_avg_price * depth * (1 + (self.commons[exchange_1 + '__' + base_asset + '-' + quote_asset].buy_fee_percentage / 100 if self.commons[exchange_1 + '__' + base_asset + '-' + quote_asset].buy_fee_asset_type == 'quote' else 0)),
                        asset_turn=base_asset,
                        amount_turn=depth * (1 - (self.commons[exchange_1 + '__' + base_asset + '-' + quote_asset].buy_fee_percentage / 100 if self.commons[exchange_1 + '__' + base_asset + '-' + quote_asset].buy_fee_asset_type == 'base' else 0)),
                        operation='trade'
                    ))
                        
                    asyncio.run(execute_emulated_balance_new(
                        name=self.emulated_balance, 
                        exchange=exchange_2,
                        asset=base_asset,
                        amount=depth,
                        asset_turn=quote_asset,
                        amount_turn=bid_avg_price * depth * (1 - (self.commons[exchange_2 + '__' + base_asset + '-' + quote_asset].sell_fee_percentage / 100)),
                        operation='trade'
                    ))
                                                
                    logging.info('-------------------CREATING TRADES FINISHES------------------- %s', self.trade_time)
                                                                        
                break
    

   
    def order_book_thread(self, exchange: str, base_asset: str, quote_asset: str, event: Event) -> None:
        thread_id = exchange + '__' + base_asset + '-' + quote_asset
        while True:
            if self.stop_check_threads[thread_id]:
                logging.info('STOPPING strategy check thread============== %s %s', self.strategy["id"], thread_id)
                self.stop_check_threads[thread_id] = False
                event.set()
                break    
            
            connection = pika.BlockingConnection(
                pika.ConnectionParameters('172.20.143.247',
                    5672,
                    '/',
                    pika.PlainCredentials('test', 'test')
                )
            )
            channel = connection.channel()
            channel.basic_consume(queue='%s.%s.%s-%s' % ('order_book', exchange, base_asset, quote_asset),
                      auto_ack=True,
                      on_message_callback=self.execution)
            channel.start_consuming()

            #self.stop_ws[thread_id] = False   
            #asyncio.run(self.execute(exchange=exchange, base_asset=base_asset, quote_asset=quote_asset, name='run_wss', attributes=(base_asset, quote_asset, 'order_book', self.stop_ws, self.execution,)))
            pair: str = base_asset + '-' + quote_asset   
            if exchange in self.order_books[pair]:
                del self.order_books[pair][exchange]
            time.sleep(3)
            logging.info('restarting order_book_thread %s %s %s', exchange, base_asset, quote_asset)
        
        
    async def fetch_balances(self, exchanges: list[str], base_asset):
        if self.testing and self.emulated_balance is not None:
            balances = await fetch_emulated_balance_new(name=self.emulated_balance)
            return balances[0]['current']
        else:
            balances: dict = {}
            for exchange in exchanges:
                balances[exchange] = await self.execute(exchange=exchange, base_asset=base_asset, quote_asset=self.quote_asset, name='fetch_balance', attributes=())
            return balances
        
async def update_balances(balances: dict):
    with open(str(Path(os.getcwd()).parent.parent) + '/base/balances_test.json', "w", encoding='UTF-8') as f:
        f.write(json.dumps(balances))
        
async def add_trades(timestamp: int, trades: dict):
    with open('trades/' + str(timestamp) + '.json', "w", encoding='UTF-8') as f:
        f.write(json.dumps(trades))

DEPTHS = {
    'USDT': {
        'min': 500,
        'max': 2000
    },
    'MX': {
        'min': 200,
        'max': 800
    },
    'BTC': {
        'min': 0.01,
        'max': 0.04
    },
    'ETH': {
        'min': 0.1,
        'max': 0.4
    },
    'SOL': {
        'min': 1,
        'max': 4
    },
    'ADA': {
        'min': 1000,
        'max': 4000
    },
    'BNB': {
        'min': 1,
        'max': 4
    },
    'DOGE': {
        'min': 3000,
        'max': 12000
    },
} 
