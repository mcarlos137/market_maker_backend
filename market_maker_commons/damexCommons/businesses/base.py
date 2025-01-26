import time
import asyncio
import logging
from threading import Thread, Event
from typing import Dict, Any
from abc import ABC, abstractmethod
import os
import json
from pathlib import Path
from logging.handlers import RotatingFileHandler
from damexCommons.base import OrderStatus, Order, OrderSide, TradeSide, Trade
from damexCommons.connectors.base import ExchangeCommons
from damexCommons.tools.bot_db import BotDB
from damexCommons.tools.dbs import get_exchange_db
from damexCommons.tools.utils import send_alert
from damexCommons.tools.damex_http_client import get_main_price, update_target

class BaseBusiness(ABC):
    
    def __init__(self, 
                 bot_id: str,
                 bot_type: str,
                 active: bool,
                 bot_db: BotDB, 
                 commons: dict[str, ExchangeCommons],
                 ) -> None:
        
        self.bot_id = bot_id
        self.bot_type = bot_type
        self.active = active
        self.bot_db = bot_db
        self.exchange_db = get_exchange_db(db_connection='exchange')
        self.commons = commons
        
        self.started = False        
        self.strategy = {}
        self.target = None
        self.stop_check_threads = {}
        self.stop_ws = {}
        
        self.initial_timestamp = int(time.time() * 1000)
        self.order_sides = [OrderSide.BID.name, OrderSide.ASK.name]
        self.active_orders: dict[str, list[Order]] = {'ASK': [], 'BID': []}
        
        
    ########### Initial function ###########
    def run(self):
        t_0 = Thread(target=self.main_thread)
        t_0.start()    
            
    ########### MAIN thread ###########
    def main_thread(self) -> None:
        while True:
            try:
                with open('config.json', encoding='UTF-8') as f:
                    config = json.load(f)
                    action = None
                    if not config['active'] and not config['restart'] and self.started:
                        action = 'stop'
                    if not config['active'] and config['restart'] and not self.started:
                        action = 'start'
                    if config['active'] and not config['restart'] and not self.started:
                        action = 'start'
                    if config['active'] and config['restart'] and self.started:
                        action = 'restart'
                        
                    if action is None:
                        continue
                    
                    match action:
                        case 'stop':
                            logging.info('STOPPING bot=====================')
                            self.started = False
                            for thread in self.stop_check_threads:
                                self.stop_check_threads[thread] = True
                            for ws in self.stop_ws:
                                self.stop_ws[ws] = True
                            time.sleep(5)    
                            for side in self.order_sides:
                                asyncio.run(self.cancel_all_orders(side=side))
                            if 'inactivate' in config['alerts']: send_alert(alert_type='bot_inactivate', message_values={
                                'id': self.bot_id,
                                'type': self.bot_type,
                                'region': config['region'],
                                'strategy': config['strategy']
                            }, channel='telegram_group_1')
                        case 'start':
                            logging.info('STARTING bot=====================')
                            with open('config.json', "w", encoding='UTF-8') as f:
                                config['active'] = True
                                config['restart'] = False
                                config['inactivation_reason'] = None
                                f.write(json.dumps(config))
                            asyncio.run(self.start())
                            if 'activate' in config['alerts']: send_alert(alert_type='bot_activate', message_values={
                                'id': self.bot_id,
                                'type': self.bot_type,
                                'region': config['region'],
                                'strategy': config['strategy']
                            }, channel='telegram_group_1')
                        case 'restart':
                            logging.info('RESTARTING bot=====================')
                            with open('config.json', "w", encoding='UTF-8') as f:
                                config['active'] = True
                                config['restart'] = False
                                config['inactivation_reason'] = None
                                f.write(json.dumps(config))
                            for thread in self.stop_check_threads:
                                self.stop_check_threads[thread] = True
                            for ws in self.stop_ws:
                                self.stop_ws[ws] = True
                            time.sleep(5)
                            for side in self.order_sides:
                                asyncio.run(self.cancel_all_orders(side=side))
                            time.sleep(5)
                            asyncio.run(self.start())
                            if 'restart' in config['alerts']: send_alert(alert_type='bot_restart', message_values={
                                'id': self.bot_id,
                                'type': self.bot_type,
                                'region': config['region'],
                                'strategy': config['strategy']
                            }, channel='telegram_group_1')
                                                                        
                time.sleep(3)
            except Exception as e:
                logging.error('main thread %s', e)
                time.sleep(1)

    ########### Basic threads ###########
    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def strategy_check_thread(self, event: Event) -> None:
        raise NotImplementedError
    
    def orders_check_thread(self, event: Event) -> None:
        while True:
            if self.stop_check_threads['orders']:
                logging.info('STOPPING orders check thread==============')
                self.stop_check_threads['orders'] = False
                event.set()
                break   
            logging.info('========== START orders check thread ==========')
            seconds_to_cancel: int = (12 * 60) if self.bot_type == 'maker' else 30
            for side in self.order_sides:       
                for active_order in self.active_orders[side].copy():
                    if active_order.creation_timestamp < (int(time.time() * 1e3) - (seconds_to_cancel * 1e3)):
                        try:
                            asyncio.run(self.cancel_order(order=active_order))
                        except Exception as e:
                             logging.error('cancel_order %s', e)
                        continue
                    order_id = None
                    try:
                        order_id = active_order.id
                        side = active_order.side
                        exchange_id = active_order.exchange_id
                        new_status = asyncio.run(self.execute(exchange=active_order.commons_exchange, base_asset=active_order.base_asset, quote_asset=active_order.quote_asset, name='fetch_order_status', attributes=(exchange_id,)))
                        match new_status:
                            case OrderStatus.CANCELLED:
                                asyncio.run(self.cancel_order(order=active_order))
                            case OrderStatus.FILLED | OrderStatus.PARTIALLY_FILLED:
                                asyncio.run(self.sync_order_trades(order=active_order, new_status=new_status))
                    except Exception as e:
                        logging.error('order_check thread %s %s %s', order_id, side, e)
                                
            logging.info('========== FINISH orders check thread ==========')                                           
            time.sleep(3)
    
    
    ########### Callbacks handler ###########
    async def execute(self, exchange: str, base_asset: str, quote_asset: str, name: str, attributes: tuple) -> Dict[str, Any]:
        key: str = exchange + '__' + base_asset + '-' + quote_asset
        return await getattr(self.commons[key], name)(*attributes)
    
    ########### Complex functions ###########
    @abstractmethod
    async def refresh_orders(self, sides: list[str]) -> None:
        raise NotImplementedError
    
    async def create_order(self, order: Order) -> None:
        try:
            exchange_id = await self.execute(exchange=order.commons_exchange, base_asset=order.base_asset, quote_asset=order.quote_asset, name='create_limit_order', attributes=(order.side.name, order.price, order.amount,))
            logging.info('exchange_id %s', exchange_id)
            if exchange_id is None:
                return
            order.exchange_id = exchange_id
            order.last_status = OrderStatus.CREATED
            order.last_update_timestamp = int(time.time() * 1e3)
            await self.bot_db.create_order_db(order=order)
            self.active_orders[order.side.name].append(order)
        except Exception as e:
            logging.error('create order %s', e)
            
    async def cancel_all_orders(self, side: str) -> None:
        orders_to_cancel = self.active_orders[side][:]
        for order_to_cancel in orders_to_cancel:
            exchange_id = None
            order_id = None
            try:
                exchange_id = order_to_cancel.exchange_id
                order_id = order_to_cancel.id
                await self.cancel_order(order=order_to_cancel)
            except Exception as e:
                logging.error('cancel order %s %s %s', order_id, exchange_id, e)
                
    async def cancel_order(self, order: Order) -> None:
        try:
            await self.sync_order_trades(order=order)
            await self.execute(exchange=order.commons_exchange, base_asset=order.base_asset, quote_asset=order.quote_asset, name='cancel_limit_order', attributes=(order.exchange_id,))
            await self.bot_db.change_order_status_db(order_id=order.id, status=OrderStatus.CANCELLED)
            logging.info('order to cancel %s', order)
            if order in self.active_orders[order.side.name]: self.active_orders[order.side.name].remove(order)
        except Exception as e:
            logging.error('cancel order %s', e)
            
    async def change_order_status(self, order: Order, new_status: OrderStatus) -> None:
        try:
            await self.bot_db.change_order_status_db(order_id=order.id, status=new_status)
            logging.info('order %s to status %s', order, new_status)
            order.last_status = new_status
            order.last_update_timestamp = int(time.time() * 1e3)
        except Exception as e:
            logging.error('change order status %s', e)
            
    async def sync_order_trades(self, order: Order, new_status: OrderStatus = None) -> None:
        try:
            order_trades = await self.execute(exchange=order.commons_exchange, base_asset=order.base_asset, quote_asset=order.quote_asset, name='fetch_order_trades', attributes=(order.exchange_id,))
            order_trades_db = await self.bot_db.fetch_order_trades_db(order_id=order.id)
            for order_trade in order_trades:
                founded = False
                for order_trade_db in order_trades_db:
                    if order_trade['id'] == order_trade_db.exchange_id:
                        founded = True
                        break
                if not founded:
                    trade = Trade(bot_id=order.bot_id, strategy_id=order.strategy_id, base_asset=order.base_asset, quote_asset=order.quote_asset, timestamp=order_trade['timestamp'], order_id=order.id, side=TradeSide.from_str(order_trade['side'].upper()), price=float(order_trade['price']), amount=float(order_trade['amount']), fee=order_trade['fee'], exchange_id=order_trade['id'], exchange=order.exchange)
                    await self.bot_db.create_trade_db(trade=trade)
                    logging.info('trade created %s', trade)
            if new_status is not None:
                await self.change_order_status(order=order, new_status=new_status)
                if new_status == OrderStatus.FILLED:
                    if order in self.active_orders[order.side.name]: self.active_orders[order.side.name].remove(order)
        except Exception as e:
            logging.error(e)
            
    ########### Refresh configurations ###########
    async def refresh_strategy_and_target(self):
        with open('config.json', encoding='UTF-8') as f:
            config = json.load(f)
            strategy_id = config['strategy']
            with open(str(Path(os.getcwd()).parent.parent) + "/strategy_files/" + strategy_id + ".json", encoding='UTF-8') as f:                   
                self.strategy['id'] = strategy_id
                strategy = json.load(f)
                for key, value in strategy.items():
                    if key == 'strategy_id' or key == 'version':
                        continue
                    if key == 'strategy_type':
                        self.strategy['type'] = value
                    self.strategy[key] = value
                
                #if self.strategy['type'] == 'maker':
                #    if 'order_price_refresh_tolerance_pct_downtrend' not in self.strategy.items():
                #        self.strategy['order_price_refresh_tolerance_pct_downtrend'] = self.strategy['order_price_refresh_tolerance_pct']
                #    if 'order_price_refresh_tolerance_pct_uptrend' not in self.strategy.items():
                #        self.strategy['order_price_refresh_tolerance_pct_uptrend'] = self.strategy['order_price_refresh_tolerance_pct']
                #    if 'order_refresh_time_downtrend' not in self.strategy.items():
                #        self.strategy['order_refresh_time_downtrend'] = self.strategy['order_refresh_time']
                #    if 'order_refresh_time_uptrend' not in self.strategy.items():
                #        self.strategy['order_refresh_time_uptrend'] = self.strategy['order_refresh_time']
                
                logging.info('strategy -> %s', self.strategy)
            if 'target' in config and config['target'] is not None:
                target_id = config['target']
                with open(str(Path(os.getcwd()).parent.parent) + "/target_files/" + target_id + ".json", encoding='UTF-8') as f:
                    self.target = {}
                    target = json.load(f)
                    for key, value in target.items():
                        self.target[key] = value
                    logging.info('target -> %s', self.target)
                                
    async def self_inactivate(self, reason: str) -> None:
        config = None
        with open('config.json', encoding='UTF-8') as f:
            config = json.load(f)
        if config is not None:
            with open('config.json', 'w', encoding='UTF-8') as f:
                config['restart'] = False
                config['active'] = False
                config['inactivation_reason'] = reason
                f.write(json.dumps(config))
                logging.info('========== INACTIVATING bot because %s ==========', reason)
                    
    
class ComplexBusiness(BaseBusiness):
    
    def __init__(self,
                bot_id: str,
                bot_type: str,
                active: bool,
                bot_db: BotDB,
                commons: dict[str, ExchangeCommons],
                exchanges: list[str], 
                base_assets: list[str],
                quote_asset: str,
                ) -> None:
        
        super().__init__(
            bot_id=bot_id,
            bot_type=bot_type,
            active=active,
            bot_db=bot_db,
            commons=commons
        )
        
        self.exchanges=exchanges
        self.base_assets=base_assets
        self.quote_asset=quote_asset
                
        self.stop_check_threads['strategy'] = False
        self.stop_check_threads['orders'] = False
        
        logging.basicConfig(
            level=logging.INFO, 
            handlers=[
                RotatingFileHandler(f"{self.bot_type}_bot__{'-'.join(self.exchanges)}__{'-'.join(self.base_assets).lower()}__{self.quote_asset.lower()}.log", mode='a', maxBytes=1024*1024*10, backupCount=10, encoding=None, delay=0),
                logging.StreamHandler()
            ],
            format="%(asctime)s %(levelname)s %(message)s"
        )
        
    def strategy_check_thread(self, event: Event) -> None:
        pass     
            
    async def refresh_orders(self, sides: list[str]) -> None:
        pass
    
                
class SimpleBusiness(BaseBusiness):
    
    def __init__(self, 
                 bot_id: str,
                 bot_type: str,
                 active: bool,
                 bot_db: BotDB, 
                 commons: dict[str, ExchangeCommons],
                 exchange: str, 
                 base_asset: str,
                 quote_asset: str,
                 tick_time: int,
                 ) -> None:
                       
        super().__init__(
            bot_id=bot_id,
            bot_type=bot_type,
            active=active,
            bot_db=bot_db,
            commons=commons
        )               
                                
        self.exchange = exchange
        self.base_asset = base_asset
        self.quote_asset = quote_asset
        self.tick_time = tick_time
        
        self.active_orders = asyncio.run(self.exchange_db.fetch_open_orders_db(base_asset=self.base_asset, quote_asset=quote_asset, exchanges=[self.exchange], bot_types=[self.bot_type], bot_id=self.bot_id, size=100))
                                                                    
        self.main_price = asyncio.run(get_main_price(base_asset=self.base_asset, quote_asset=self.quote_asset, price_decimals=self.commons[self.exchange + '__' + self.pair].price_decimals))
        self.main_price_timestamp = int(time.time() * 1e3)
        
        self.stop_check_threads['strategy'] = False
        self.stop_check_threads['orders'] = False
        self.stop_check_threads['balance_1h'] = False
        self.stop_check_threads['target'] = False
        
        self.balance_1h_start = None
        self.balance_1h_timestamp = None
        
        logging.basicConfig(
            level=logging.INFO, 
            handlers=[
                RotatingFileHandler(f"{self.bot_type}_bot_{self.exchange}_{self.base_asset.lower()}{self.quote_asset.lower()}.log", mode='a', maxBytes=1024*1024*10, backupCount=10, encoding=None, delay=0),
                logging.StreamHandler()
            ],
            format="%(asctime)s %(levelname)s %(message)s"
        )
        
    @property
    def pair(self) -> str:
        return self.base_asset + '-' + self.quote_asset
    
    @property
    def exchange_aux(self) -> str:
        return self.exchange + '_aux'
        
    ########### Basic threads ###########
    def balance_1h_check_thread(self, event: Event) -> None:  
         while True:
            if self.stop_check_threads['balance_1h']:
                logging.info('STOPPING balance 1h check thread==============')
                self.stop_check_threads['balance_1h'] = False
                event.set()
                break        
            logging.info('========== START balance 1h check thread ==========')
            try:
                timestamp = int(time.time() * 1e3)
                if self.balance_1h_timestamp is None or timestamp - (60 * 60 * 1e3) > self.balance_1h_timestamp:
                    balance = asyncio.run(self.execute(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, name='fetch_balance', attributes=()))
                    total_base_amount = float(balance[self.base_asset]['total'])
                    total_quote_amount = float(balance[self.quote_asset]['total'])
                    self.balance_1h_start = {self.base_asset: total_base_amount, self.quote_asset: total_quote_amount}
                    self.balance_1h_timestamp = timestamp
                logging.info('========== FINISH balance 1h check thread ==========')
            except Exception as e:
                logging.error('balance_1h_check thread %s', e)
            time.sleep(2)
            
    def target_check_thread(self, event: Event) -> None:  
        while True:
            if self.stop_check_threads['target']:
                logging.info('STOPPING target check thread==============')
                self.stop_check_threads['target'] = False
                event.set()
                break        
            logging.info('========== START target check thread ==========')
            try:
                balance = asyncio.run(self.execute(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, name='fetch_balance', attributes=()))
                total_base_amount = float(balance[self.base_asset]['total'])
                if self.target is not None and self.target['asset'] == self.base_asset:
                    if self.target['operation'] == TradeSide.BUY.name:
                        base_asset_diff = total_base_amount - self.target['initial_asset_amount']
                        base_asset_diff += self.commons[self.exchange + '__' + self.pair].base_min_amount
                        if base_asset_diff >= self.target['operation_amount']:
                            time.sleep(15)
                            asyncio.run(update_target(target_id=self.target['target_id'], status='completed'))
                            asyncio.run(self.self_inactivate(reason='target reached'))
                    
                    if self.target['operation'] == TradeSide.SELL.name:
                        base_asset_diff = self.target['initial_asset_amount'] - total_base_amount
                        base_asset_diff += self.commons[self.exchange + '__' + self.pair].base_min_amount
                        if base_asset_diff >= self.target['operation_amount']:
                            time.sleep(15)
                            asyncio.run(update_target(target_id=self.target['target_id'], status='completed'))
                            asyncio.run(self.self_inactivate(reason='target reached'))
                        
                logging.info('========== FINISH target check thread ==========')
            except Exception as e:
                logging.error('target_check thread %s', e)
            time.sleep(2)
        
    async def refresh_orders(self, sides: list[str]) -> None:
        pass