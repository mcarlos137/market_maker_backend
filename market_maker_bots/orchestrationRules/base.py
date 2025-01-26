import time
from threading import Thread, Event
import json
import asyncio
import itertools
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import pytz
from typing import Any, Optional
import os
import sys
sys.path.append(os.getcwd())
from damexCommons.base import Trade
from damexCommons.connectors.base import ExchangeCommons
from damexCommons.tools.exchange_db import ExchangeDB
#from damexCommons.tools.exchange import get_main_price
from damexCommons.tools.dbs import get_exchange_db
from damexCommons.tools.utils import send_alert, write_to_google_spreadsheet
from damexCommons.tools.damex_http_client import fetch_target, change_bot_target, change_bot_strategy, change_bot_status
from damexCommons.tools.connections import get_commons


class OrchestrationRulesBase:
    
    def __init__(self, 
                orchestration_rule_id: str, 
                exchanges_apis: dict,
                start_time: str,
                active: bool, 
                members: list, 
                tick_time: int,
                excluded_days: list[str],
                target_initial_timestamp: int = None
                ) -> None:
        
        self.orchestration_rule_id=orchestration_rule_id
        self.exchanges_apis=exchanges_apis
        self.start_time=start_time
        self.active=active
        self.members=members
        self.tick_time=tick_time
        self.excluded_days=excluded_days
        self.target_initial_timestamp=target_initial_timestamp
                

class OrchestrationRules:
    
    def __init__(self, orchestration_rules_base: OrchestrationRulesBase) -> None:
        
        self.orchestration_rule_id=orchestration_rules_base.orchestration_rule_id
        self.exchanges_apis=orchestration_rules_base.exchanges_apis
        self.start_time=orchestration_rules_base.start_time
        self.active=orchestration_rules_base.active
        self.members=orchestration_rules_base.members
        self.target_initial_timestamp=orchestration_rules_base.target_initial_timestamp
        self.tick_time=orchestration_rules_base.tick_time
        self.excluded_days=orchestration_rules_base.excluded_days
               
        self.commons: dict[str, ExchangeCommons] = {}
                
        self.exchange_db: ExchangeDB = get_exchange_db(db_connection='exchange')
                                                                          
        self.stop_rules_check_thread = False
                
        self.target = None
        self.started = False
        
        self.rules = []
        
        self.target = None
        
        self.initial_day_timestamp = None
        self.initial_sleep_timestamp = {}
                
        logging.basicConfig(
            level=logging.INFO, 
            handlers=[
                RotatingFileHandler(f"orchestration_rule_{self.orchestration_rule_id}.log", mode='a', maxBytes=1024*1024*10, backupCount=10, encoding=None, delay=0),
                logging.StreamHandler()
            ],
            format="%(asctime)s %(levelname)s %(message)s"
        )
        
    @property
    def get_target_id(self) -> str:
        if self.target_initial_timestamp is None:
            return None
        return 'or_' + self.orchestration_rule_id + '_' + str(self.target_initial_timestamp)
                     
    def run(self):
        t_0 = Thread(target=self.main_thread)
        t_0.start()

        
    def main_thread(self) -> None:
        while True:
            try:      
                config = None
                with open('config.json', encoding='UTF-8') as f:
                    config = json.load(f)
                    if self.start_time != config['start_time']:
                        self.start_time = config['start_time']
                        asyncio.run(self.refresh_rules())
                        self.target_initial_timestamp = None
                    self.excluded_days = config['excluded_days']
                
                initial_day_timestamp = int(datetime.now(pytz.timezone('UTC')).replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
                day = datetime.fromtimestamp(initial_day_timestamp / 1e3).strftime('%A')
                if self.initial_day_timestamp is None or self.initial_day_timestamp < initial_day_timestamp:
                    logging.info('starting new day %s', day) 
                    asyncio.run(self.refresh_rules())
                    self.initial_day_timestamp = initial_day_timestamp
                    self.target_initial_timestamp = None
                
                if len(self.excluded_days) > 0 and day in self.excluded_days and self.started:
                    logging.info('Execution excluded on %s', day) 
                    self.rules = []
                    time.sleep(5)
                    continue

                action = None
                
                if not config['active'] and not config['restart'] and self.started:
                    action = 'stop'
                
                if not config['active'] and config['restart'] and not self.started:
                    action = 'start'
                
                if config['active'] and not config['restart'] and not self.started:
                    action = 'start'
                
                if config['active'] and config['restart'] and self.started:
                    action = 'restart'
                
                # If there is a target, this will check if OR is running to stop it at failed state or change rules at completed state
                if self.get_target_id is not None:
                    target = asyncio.run(fetch_target(target_id=self.get_target_id))
                    if 'status' in target and target['status'] == 'failed' and self.started:
                        self.rules = []
                
                # Avoid to start or restart if first rule is in the past            
                if len(self.rules) > 0:
                    for rule in self.rules:
                        if rule['type'] == 'time':
                            milliseconds_left_to_next_rule = int(self.rules[0]['value'].split('__')[1]) - int(time.time() * 1e3)
                            if milliseconds_left_to_next_rule < 0:
                                if action in ['start', 'restart']:
                                    action = None
                
                if action is None:
                    time.sleep(3)
                    continue
                
                match action:
                    case 'stop':
                        logging.info('STOPPING orchestration rule=====================')
                        self.started = False
                        self.rules = []
                        self.stop_rules_check_thread = True
                        self.initial_day_timestamp = None
                        self.target_initial_timestamp = None
                        with open('config.json', "w", encoding='UTF-8') as f:
                            config['target_initial_timestamp'] = self.target_initial_timestamp
                            config['active'] = False
                            config['restart'] = False
                            f.write(json.dumps(config))
                        if 'inactivate' in config['alerts']: send_alert(alert_type='or_action', message_values={
                            'id': self.orchestration_rule_id,
                            'region': 'ireland',
                            'strategy': config['strategy'],
                            'action': 'INACTIVATED'
                        }, channel='telegram_group_1')
                    case 'start':
                        logging.info('STARTING orchestration rule=====================')
                        with open('config.json', "w", encoding='UTF-8') as f:
                            config['target_initial_timestamp'] = self.target_initial_timestamp
                            config['active'] = True
                            config['restart'] = False
                            f.write(json.dumps(config))
                        asyncio.run(self.start())
                        if 'activate' in config['alerts']: send_alert(alert_type='or_action', message_values={
                            'id': self.orchestration_rule_id,
                            'region': 'ireland',
                            'strategy': config['strategy'],
                            'action': 'ACTIVATED'
                        }, channel='telegram_group_1')
                    case 'restart':
                        logging.info('RESTARTING orchestration rule=====================')
                        asyncio.run(self.refresh_rules())
                        with open('config.json', "w", encoding='UTF-8') as f:
                            config['target_initial_timestamp'] = self.target_initial_timestamp
                            config['active'] = True
                            config['restart'] = False
                            f.write(json.dumps(config))
                        if 'restart' in config['alerts']: send_alert(alert_type='or_action', message_values={
                            'id': self.orchestration_rule_id,
                            'region': 'ireland',
                            'strategy': config['strategy'],
                            'action': 'RESTARTED'
                        }, channel='telegram_group_1')
                    
                time.sleep(3)
            except Exception as e:
                logging.error('main thread %s', e)
                time.sleep(1)
                
    async def start(self) -> None:
        t_1 = Thread(target=self.rules_check_thread, args=(Event(),))
        t_1.start()                            
            
        if not self.started:
            self.started = True
    
    ####### custom threads                    
    def rules_check_thread(self, event: Event) -> None:
        while True:
            if self.stop_rules_check_thread:
                logging.info('STOPPING rules check thread============== %s', self.orchestration_rule_id)
                self.stop_rules_check_thread = False
                event.set()
                break            
            try:                
                logging.info('========== START rules check thread ========== %s', self.orchestration_rule_id) 
                
                if len(self.rules) > 0:   
                    for rule in self.rules:
                        if rule['type'] == 'time':
                            milliseconds_left_to_next_rule = int(self.rules[0]['value'].split('__')[1]) - int(time.time() * 1e3)
                            logging.info('seconds left to next rule %s', round(milliseconds_left_to_next_rule / 1e3, 0)) 
                            break
                logging.info('rules %s', self.rules) 
                
                asyncio.run(self.check_target_rules())

                logging.info('========== FINISH rules check thread ========== %s', self.orchestration_rule_id) 
                time.sleep(self.tick_time)
            except Exception as e:
                logging.error('rules check thread %s', e)
                time.sleep(1)
                
    ####### custom methods
    async def set_target(self, balance: dict, period_in_milliseconds: int) -> None:
        raise NotImplementedError
                       
    async def check_target_rules(self) -> None:
        on_target_completed = False
        if self.get_target_id is not None:
            target = await fetch_target(target_id=self.get_target_id)
            if 'status' in target and target['status'] == 'completed' and self.started:
                on_target_completed = True
        current_time = int(time.time() * 1e3)
        stop_loop = False
        
        for rule in self.rules[:]:
            rule_id = rule['id']
            rule_type = rule['type']
            value = rule['value']
            member = rule['member']
            apply_on_target_completed = rule['apply_on_target_completed']
            if on_target_completed and not apply_on_target_completed:
                self.rules = [rule for rule in self.rules if rule['id'] != rule_id]
                continue
            key: str = None            
            match rule_type:
                case 'time':
                    period = value.split('__')[0]
                    new_time = int(value.split('__')[1])
                    if not on_target_completed and (current_time < new_time or current_time > new_time + (3 * 60 * 1e3)):
                        continue
                    key = period + '__' + str(new_time)
                case 'continuous':
                    action_type = value.split('__')[0]
                    if action_type == 'SLEEP':
                        period = value.split('__')[1]
                        sleep_key = 'rule_' + rule_id
                        sleep_period = await self.get_period_in_milliseconds(period=period)
                        timestamp = int(time.time() * 1e3)   
                        if not sleep_key in self.initial_sleep_timestamp or timestamp - sleep_period > self.initial_sleep_timestamp[sleep_key]:
                            self.initial_sleep_timestamp[sleep_key] = timestamp
                        else:
                            continue
                        #key = sleep_key + '__' + str(timestamp)
            for action in rule['actions'][:]:
                action_parts: list = action.split('__')
                action_object = action_parts[0]
                action_verb =action_parts[1]
                if key is not None:
                    key += '__' + member + '__' + action
                rules_applied = None
                with open('rules_applied.json', encoding='UTF-8') as f:
                    rules_applied = json.load(f)
                    if key in rules_applied:
                        logging.info('rule %s already applied', key) 
                        stop_loop = True
                        continue
                match action_object:
                    
                    case 'bot':
                        match action_verb:
                            case 'add_target':
                                logging.info('adding bot target %s', self.get_target_id) 
                                await change_bot_target(bot_id=member.split('_')[1], bot_type=member.split('_')[0], region=member.split('_')[2], target=self.get_target_id)
                            case 'change_strategy':
                                action_params = action_parts[2]
                                logging.info('changing member %s %s strategy to %s', member.split("_")[0], member.split("_")[1], action_params)    
                                await change_bot_strategy(bot_id=member.split('_')[1], bot_type=member.split('_')[0], region=member.split('_')[2], strategy=action_params)
                            case 'change_status':     
                                action_params = action_parts[2]                        
                                logging.info('changing member %s %s status to %s', member.split("_")[0], member.split("_")[1], action_params)         
                                await change_bot_status(bot_id=member.split('_')[1], bot_type=member.split('_')[0], region=member.split('_')[2], action=action_params)   
                            case 'change_strategy_cobwmp':                                
                                action_params = action_parts[2]
                                exchange = str(action_params.split('_')[0])
                                base_asset = str(action_params.split('_')[1])
                                quote_asset = str(action_params.split('_')[2])
                                range_percentage = action_params.split('_')[3].replace('range[', '').replace(']', '').split(',')
                                strategy = str(action_params.split('_')[4])
                                
                                print('-------------', exchange, base_asset, quote_asset, range_percentage, strategy)
                                order_book = asyncio.run(self.execute(exchange=exchange, base_asset=base_asset, quote_asset=quote_asset, name='fetch_order_book', attributes=())) 
                                if len(order_book['asks']) > 0 and len(order_book['bids']) > 0:
                                    first_ask_order_price = float(order_book['asks'][0][0])
                                    first_bid_order_price = float(order_book['bids'][0][0])
                                    logging.info('first ASK order price %s', str(first_ask_order_price))
                                    logging.info('first BID order price %s', str(first_bid_order_price))
                                    
                                    '''
                                    main_price = await get_main_price(base_asset=base_asset, quote_asset=quote_asset)
                                    
                                    if first_ask_order_price < main_price:
                                        print('-------- order book price is lower than main price' )
                                        diff = (first_ask_order_price - main_price) * 100 / main_price
                                    elif first_bid_order_price > main_price:
                                        print('-------- order book price is higher than main price' )
                                        diff = (first_bid_order_price - main_price) * 100 / main_price
                                    else:
                                        print('-------- NORMAL' )
                                    '''
                                #logging.info('changing member %s %s strategy to %s', member.split("_")[0], member.split("_")[1], action_params)    
                                
                                #await change_bot_strategy(bot_id=member.split('_')[1], bot_type=member.split('_')[0], region=member.split('_')[2], strategy=strategy)
                
                    case 'or':
                        match action_verb:
                            case 'create_target':
                                logging.info('creating OR target %s', self.get_target_id) 
                                await self.refresh_target()
                                current_timestamp = int(time.time() * 1e3)
                                match self.target['period']:
                                    case 'DAILY':
                                        period_in_milliseconds = int(24 * 60 * 60 * 1e3)
                                    case 'HOURLY':
                                        period_in_milliseconds = int(1 * 60 * 60 * 1e3)
                                exchange = self.target['exchange']
                                balance = await self.execute(exchange=exchange, base_asset=self.target['base_asset'], quote_asset=self.target['quote_asset'], name='fetch_balance', attributes=())
                                try:
                                    self.target_initial_timestamp = current_timestamp
                                    await self.change_config({
                                        'target_initial_timestamp': self.target_initial_timestamp,
                                    })
                                    await self.set_target(balance=balance, period_in_milliseconds=period_in_milliseconds)
                                except Exception:
                                    continue
                            case 'compare_balance':
                                action_params = action_parts[2]
                                logging.info('comparing OR balance %s', action_params)                                         
                                exchange = str(action_params.split('_')[0])
                                asset = str(action_params.split('_')[1])
                                compare_type = str(action_params.split('_')[2])
                                compare = str(action_params.split('_')[3])
                                amount = float(action_params.split('_')[4])
                                or_action = str(action_params.split('_')[5])
                                execute_or_action = False                            
                                balance = await self.execute(exchange=exchange, base_asset=asset, quote_asset='NONE', name='fetch_balance', attributes=())
                                asset_balance = float(balance[asset][compare_type])
                                match compare:
                                    case 'lower':
                                        if amount > asset_balance:
                                            execute_or_action = True
                                    case 'higher':    
                                        if amount < asset_balance:
                                            execute_or_action = True
                                if execute_or_action:
                                    if 'rules' in or_action:
                                        new_rules = or_action.replace('rules[', '').replace(']', '').split(',')
                                        await self.refresh_rules(current_time=int(time.time() * 1e3), only_ids=new_rules)
                                        stop_loop = True    
                            case 'start_balance_emulation_2_exchanges_2_assets':
                                action_params = action_parts[2]
                                exchange_1 = str(action_params.split('_')[0])
                                #exchange_1_asset_1 = str(action_params.split('_')[1])
                                #exchange_1_amount_1 = float(action_params.split('_')[2])
                                #exchange_1_asset_2 = str(action_params.split('_')[3])
                                #exchange_1_amount_2 = float(action_params.split('_')[4])
                                exchange_2 = str(action_params.split('_')[5])
                                #exchange_2_asset_1 = str(action_params.split('_')[6])
                                #exchange_2_amount_1 = float(action_params.split('_')[7])
                                #exchange_2_asset_2 = str(action_params.split('_')[8])
                                #exchange_2_amount_2 = float(action_params.split('_')[9])                                
                                        
                    case 'alert':
                        match action_verb:
                            case 'send_status':
                                logging.info('sending status alert')
                                await self.send_status_alert(channel=member)
                            case 'send_balance':
                                action_params = action_parts[2]
                                logging.info('sending balance alert %s', action_params)
                                exchange = action_params.split('_')[0]
                                base_asset = action_params.split('_')[1]
                                quote_asset = action_params.split('_')[2]
                                balance = await self.execute(exchange=exchange, base_asset=base_asset, quote_asset=quote_asset, name='fetch_balance', attributes=())
                                await self.send_balance_alert(channel=member, exchange=exchange, base_asset=base_asset, quote_asset=quote_asset, base_amount=round(float(balance[base_asset]['total']), self.commons[exchange + '__' + base_asset + '-' + quote_asset].base_amount_decimals), quote_amount=round(float(balance[quote_asset]['total']), self.commons[exchange + '__' + base_asset + '-' + quote_asset].quote_amount_decimals))   
                            case 'send_trades_sell_report':
                                action_params = action_parts[2]
                                logging.info('sending trades sell report alert %s', action_params)
                                template = action_params.split('_')[0]
                                exchange = action_params.split('_')[1]
                                base_asset = action_params.split('_')[2]
                                quote_asset = action_params.split('_')[3]
                                trades: list[Trade] = await self.exchange_db.fetch_trades_db(
                                            exchanges=[exchange],
                                            base_asset=base_asset,
                                            quote_asset=quote_asset,
                                            initial_timestamp=self.target_initial_timestamp,
                                            sides=[2],
                                            order_timestamp='DESC',
                                        )
                                await self.send_trades_sell_report_alert(channel=member, template=template, exchange=exchange, base_asset=base_asset, quote_asset=quote_asset, trades=trades) 
                            case 'send_arbitrage_candidate':
                                action_params = action_parts[2]
                                logging.info('sending arbitrage candidate alert %s', action_params)    
                                base_asset = action_params.split('_')[0]
                                quote_asset = action_params.split('_')[1]
                                expenses_percentage = float(action_params.split('_')[2])
                                min_profitability = float(action_params.split('_')[3])
                                min_depth = float(action_params.split('_')[4])
                                max_depth = float(action_params.split('_')[5])
                                exchanges = action_params.split('_')[6].replace('exchanges[', '').replace(']', '').split(',')
                                exchange_groups = list(itertools.combinations(exchanges, 2))
                                for exchange_group in exchange_groups:
                                    exchange_combinations = [
                                        {'exchange_1': exchange_group[0], 'exchange_2': exchange_group[1]},
                                        {'exchange_1': exchange_group[1], 'exchange_2': exchange_group[0]}
                                    ]
                                    order_books = {}
                                    for exchange_combination in exchange_combinations:
                                        exchange_1 = exchange_combination['exchange_1']
                                        exchange_2 = exchange_combination['exchange_2']
                                        logging.info('comparing %s with %s', exchange_1, exchange_2)
                                        try:
                                            if exchange_1 not in order_books:
                                                order_books[exchange_1] = await self.execute(exchange=exchange_1, base_asset=base_asset, quote_asset=quote_asset, name='fetch_order_book', attributes=())
                                            if exchange_2 not in order_books:
                                                order_books[exchange_2] = await self.execute(exchange=exchange_2, base_asset=base_asset, quote_asset=quote_asset, name='fetch_order_book', attributes=())
                                        except Exception as e:
                                            logging.error('%s', e)
                                            continue
                                        logging.info('first %s ASK %s', exchange_1, order_books[exchange_1]["asks"][0])
                                        logging.info('first %s BID %s', exchange_2, order_books[exchange_2]["bids"][0])
                                        bid_levels = 0
                                        total_bid_amount = 0
                                        bids_price_per_amount_sum = 0
                                        first_ask_price = float(order_books[exchange_1]['asks'][0][0])
                                        for bid in order_books[exchange_2]['bids']:
                                            bid_price = float(bid[0])
                                            bid_amount = float(bid[1])
                                            if first_ask_price * (1 + (expenses_percentage / 100)) < bid_price:
                                                bids_price_per_amount_sum += bid_price * bid_amount
                                                total_bid_amount += bid_amount
                                                if bids_price_per_amount_sum > max_depth:
                                                    bids_price_per_amount_sum -= bid_price * bid_amount
                                                    total_bid_amount -= bid_amount
                                                    bids_price_per_amount_sum += bid_price * (max_depth - total_bid_amount)
                                                    total_bid_amount += (max_depth - total_bid_amount)
                                                bid_levels += 1
                                            else:
                                                break
                                        ask_levels = 0
                                        total_ask_amount = 0
                                        asks_price_per_amount_sum = 0
                                        first_bid_price = float(order_books[exchange_2]['bids'][0][0])
                                        for ask in order_books[exchange_1]['asks']:
                                            ask_price = float(ask[0])
                                            ask_amount = float(ask[1])
                                            if first_bid_price > ask_price * (1 + (expenses_percentage / 100)):
                                                asks_price_per_amount_sum += ask_price * ask_amount
                                                total_ask_amount += ask_amount
                                                if asks_price_per_amount_sum > max_depth:
                                                    asks_price_per_amount_sum -= ask_price * ask_amount
                                                    total_ask_amount -= ask_amount
                                                    asks_price_per_amount_sum += ask_price * (max_depth - total_ask_amount)
                                                    total_ask_amount += (max_depth - total_ask_amount)
                                                ask_levels += 1
                                        depth = total_bid_amount
                                        levels = bid_levels
                                        if total_ask_amount < depth:
                                            depth = total_ask_amount
                                            levels = ask_levels
                                        if depth < min_depth:
                                            logging.info('min depth is not reached')
                                            continue
                                        ask_avg_price = asks_price_per_amount_sum / total_ask_amount
                                        bid_avg_price = bids_price_per_amount_sum / total_bid_amount
                                        arb_opportunity = bid_avg_price - ask_avg_price      
                                        profitability = (arb_opportunity * 100 / ask_avg_price) - expenses_percentage
                                        if profitability < min_profitability:
                                            logging.info('min profitability is not reached')
                                            continue
                                        profit = round(float(depth * arb_opportunity * (1 - expenses_percentage / 100)), self.commons[exchange_1 + '__' + base_asset + '-' + quote_asset].quote_amount_decimals)
                                        await self.send_arbitrage_candidate_alert(channel=member, 
                                                                                  exchange_1=exchange_1, 
                                                                                  exchange_2=exchange_2,
                                                                                  base_asset=base_asset,
                                                                                  quote_asset=quote_asset,
                                                                                  price_buy_1=ask_avg_price,
                                                                                  price_sell_2=bid_avg_price,
                                                                                  depth=depth,
                                                                                  levels=levels,
                                                                                  arb_opportunity=arb_opportunity,
                                                                                  profitability=profitability,
                                                                                  profit=profit
                                                                                  )
                                        break

                    case 'data':
                        match action_verb:
                            case 'export_all_trades':
                                action_params = action_parts[2]
                                logging.info('exporting data to document %s %s', member, action_params)
                                template = action_params.split('_')[0]
                                exchange = action_params.split('_')[1]
                                base_asset = action_params.split('_')[2]
                                quote_asset = action_params.split('_')[3]
                                match template:
                                    case 'details' | 'resume':
                                        trades: list[Trade] = await self.exchange_db.fetch_trades_db(
                                            exchanges=[exchange],
                                            base_asset=base_asset,
                                            quote_asset=quote_asset,
                                            initial_timestamp=self.target_initial_timestamp,
                                            sides=[1, 2],
                                            order_timestamp='DESC',
                                        )
                                        await self.export_all_trades(base_asset=base_asset, quote_asset=quote_asset, trades=trades, member=member, template=template)
                
                if key is not None:                                    
                    rules_applied[key] = current_time
                    rule['actions'].remove(action)
                    with open('rules_applied.json', 'w', encoding='UTF-8') as f:
                        f.write(json.dumps(rules_applied))
                if stop_loop:
                    break
                time.sleep(3)
            if key is not None:
                self.rules = [rule for rule in self.rules if rule['id'] != rule_id]
            if stop_loop:
                break    
                
    async def refresh_target(self):
        with open('target.json', encoding='UTF-8') as f:
            self.target = json.load(f)
        logging.info('target -> %s', self.target)  
                        
    async def refresh_rules(self, current_time: int = None, only_ids: Optional[list] = [], only_on_complete_target: Optional[bool] = False):
        with open('rules.json', encoding='UTF-8') as f:
            basic_rules = json.load(f)                
            start_time = int(datetime.now(pytz.timezone('UTC')).replace(hour=int(self.start_time.split(':')[0]), minute=int(self.start_time.split(':')[1]), second=int(self.start_time.split(':')[2]), microsecond=0).timestamp() * 1000)
            if current_time is not None:
                start_time = current_time
            logging.info('start_time -> %s', str(datetime.fromtimestamp(start_time / 1e3).time()))
            previous_time = start_time
            self.rules = []
            for basic_rule in basic_rules:      
                rule_id = basic_rule['id']
                rule_type = basic_rule['type']
                value = basic_rule['value']
                if len(only_ids) > 0 and rule_id not in only_ids:
                    continue
                if only_on_complete_target and not basic_rule['apply_on_target_completed']:
                    continue
                match rule_type:
                    case 'delay':
                        delay_from = value.split('__')[0]
                        delay_period = value.split('__')[1]
                        if delay_from == 'START':
                            delay_period_time = await self.get_period_in_milliseconds(period=delay_period)
                            rule_time = start_time + delay_period_time
                        elif delay_from == 'PREV':
                            delay_period_time = await self.get_period_in_milliseconds(period=delay_period)
                            rule_time = previous_time + delay_period_time
                        rule = {
                            'id': rule_id,
                            'type': 'time',
                            'value': 'DAY__' + str(rule_time),
                            'actions': basic_rule['actions'],
                            'member': basic_rule['member'],
                            'apply_on_target_completed': basic_rule['apply_on_target_completed'],
                        }
                        self.rules.append(rule)
                        previous_time = rule_time
                        
                    case 'time' | 'continuous':
                        rule = {
                            'id': rule_id,
                            'type': rule_type,
                            'value': value,
                            'actions': basic_rule['actions'],
                            'member': basic_rule['member'],
                            'apply_on_target_completed': basic_rule['apply_on_target_completed'],
                        }
                        self.rules.append(rule)
            logging.info('rules -> %s', self.rules)
        
    async def get_period_in_milliseconds(self, period: str):
        if 's' in period:
            return int(int(period.replace('s', '')) * 1e3)
        elif 'm' in period:
            return int(int(period.replace('m', '')) * 60 * 1e3)
        elif 'h' in period:
            return int(int(period.replace('h', '')) * 60 * 60 * 1e3)
        return 0
    
    async def change_config(self, new_params: dict):
        with open('config.json', encoding='UTF-8') as f:
            config = json.load(f)
        config.update(new_params)
        with open('config.json', 'w', encoding='UTF-8') as f:
            f.write(json.dumps(config))
                        
    async def export_all_trades(self, base_asset: str, quote_asset: str, trades: list[Trade], member: str, template: str) -> None:
        if len(trades) == 0:
            return  
        match member:
            case 'spreadsheet_main_1' | 'spreadsheet_main_2':
                spreadsheet_id = None
                if member == 'spreadsheet_main_1':
                    #spreadsheet_id = '1W30ihejsSSLZ9MjkAvD4tWn8sAiKbOJnq_GZMwluHr8'
                    spreadsheet_id = '1-_UfMnlYrHbP6KfV4CVb9htLHI2hjHrU7PstW0IKSQQ'
                elif member == 'spreadsheet_main_2':
                    spreadsheet_id = None
                if spreadsheet_id is None:
                    return
                values: list[list] = []
                for trade in trades:
                    values.append([datetime.fromtimestamp(trade.timestamp / 1e3).isoformat(), trade.side, trade.price, trade.amount, str(trade.fee)])
                new_values: list[list] = []
                sheet_id = None
                match template:
                    case 'details':
                        #sheet_id = 'details'
                        sheet_id = 'Bot sale details'
                        new_values = values
                    case 'resume':
                        #sheet_id = 'resume'
                        sheet_id = 'Bot sale history'
                        dates: list = []
                        trade_type = f'SELL {base_asset} to {quote_asset}'
                        date = None
                        avg_price = 0
                        fee = 0
                        base_amount = 0
                        quote_amount = 0
                        after_exchange_fee = 0
                        for value in values:
                            new_date = str(value[0]).split('T')[0]
                            value[4] = str(value[4]).replace("'", '"')
                            new_fee = json.loads(value[4])
                            if date is None or new_date != date:
                                date = new_date
                                dates.append(date)
                                new_values.append([trade_type, date, avg_price, fee, base_amount, quote_amount, after_exchange_fee])
                            new_value = [new_value for new_value in new_values if new_value[1] == date][0]
                            new_value[3] += new_fee['cost']
                            new_value[4] += value[3]
                            new_value[5] += value[2] * value[3] 
                            new_value[6] += (value[2] * value[3]) - new_fee['cost']
                            [new_value for new_value in new_values if new_value[1] == date][0] = new_value  
                        for date in dates:
                            [new_value for new_value in new_values if new_value[1] == date][0][2] = [new_value for new_value in new_values if new_value[1] == date][0][6] / [new_value for new_value in new_values if new_value[1] == date][0][4]
                write_to_google_spreadsheet(spreadsheet_id=spreadsheet_id, values=new_values, sheet_id=sheet_id)
                
    async def get_status(self, target: dict):
        if self.get_target_id is None:
            return 'NOT DEFINED YET'
        status: str = 'RUNNING'
        target_completed = False
        target_failed = False
        if 'status' in target:
            target_completed = target['status'] == 'completed'
            target_failed = target['status'] == 'failed'
        if target_completed:
            status = 'COMPLETED'
        elif target_failed:
            status = 'TARGET FAILED'
        elif len(await self.get_bot_rules()) == 0:
            status = 'COMPROMISED'
        current_time = int(time.time() * 1e3)
        start_time = int(datetime.now(pytz.timezone('UTC')).replace(hour=int(self.start_time.split(':')[0]), minute=int(self.start_time.split(':')[1]), second=int(self.start_time.split(':')[2]), microsecond=0).timestamp() * 1000)
        if start_time > current_time:
            status = 'IDLE'
        return status
            
    async def send_status_alert(self, channel):
        if self.get_target_id is None:
            return
        target = await fetch_target(target_id=self.get_target_id)
        status = await self.get_status(target=target)
        base_amount_decimals = await self.exchange_db.get_asset_decimals(asset=target['asset'])
        send_alert(alert_type='or_status', message_values={
            'target_id': target['target_id'],
            'asset': target['asset'],
            'operation': target['operation'],
            'op_amount': f"%.{base_amount_decimals}f" % round(target['operation_amount'], base_amount_decimals),
            'status': status
        }, channel=channel)
    
    async def send_balance_alert(self, channel: str, exchange: str, base_asset: str, quote_asset: str, base_amount: float, quote_amount: float):
        base_amount_decimals =  self.commons[exchange + '__' + base_asset + '-' + quote_asset].base_amount_decimals
        quote_amount_decimals = self.commons[exchange + '__' + base_asset + '-' + quote_asset].quote_amount_decimals
        send_alert(alert_type='balance', message_values={
            'exchange': exchange,
            'base_asset': base_asset,
            'quote_asset': quote_asset,
            'base_amount': f"%.{base_amount_decimals}f" % round(base_amount, base_amount_decimals),
            'quote_amount': f"%.{quote_amount_decimals}f" % round(quote_amount, quote_amount_decimals),
        }, channel=channel)
    
    async def send_trades_sell_report_alert(self, channel: str, template: str, exchange: str, base_asset: str, quote_asset: str, trades: list[Trade]):
        pair: str = base_asset + '-' + quote_asset
        await self.execute(exchange=exchange, base_asset=base_asset, quote_asset=quote_asset, name='NONE', attributes=())
        base_amount_decimals =  self.commons[exchange + '__' + pair].base_amount_decimals
        quote_amount_decimals = self.commons[exchange + '__' + pair].quote_amount_decimals  
        price_decimals = self.commons[exchange + '__' + pair].price_decimals
        
        trades_size = {'ALL': len(trades)}
        price_by_amount_sum = {'ALL': 0}
        amount_sum = {'ALL': 0}
        base_fee_sum = {'ALL': 0}
        quote_fee_sum = {'ALL': 0}
        
        for trade in trades:
            if trade.strategy_id not in trades_size:
                trades_size[trade.strategy_id] = 0
            trades_size[trade.strategy_id] += 1
            
            price_by_amount_sum['ALL'] += trade.price * trade.amount
            if trade.strategy_id not in price_by_amount_sum:
                price_by_amount_sum[trade.strategy_id] = 0
            price_by_amount_sum[trade.strategy_id] += trade.price * trade.amount
                    
            amount_sum['ALL'] += trade.amount
            if trade.strategy_id not in amount_sum:
                amount_sum[trade.strategy_id] = 0
            amount_sum[trade.strategy_id] += trade.amount
            
            if base_asset == trade.fee['currency']:
                base_fee_sum['ALL'] += float(trade.fee['cost'])
                if trade.strategy_id not in base_fee_sum:
                    base_fee_sum[trade.strategy_id] = 0
                base_fee_sum[trade.strategy_id] += float(trade.fee['cost'])
                        
            elif quote_asset == trade.fee['currency']:
                quote_fee_sum['ALL'] += float(trade.fee['cost'])
                if trade.strategy_id not in quote_fee_sum:
                    quote_fee_sum[trade.strategy_id] = 0
                quote_fee_sum[trade.strategy_id] += float(trade.fee['cost'])
                
        match template:
            case 'default' | 'client1':
                base_amount = round(float(amount_sum['ALL']) - float(base_fee_sum['ALL']), base_amount_decimals)
                quote_amount = round(float(price_by_amount_sum['ALL']) - float(quote_fee_sum['ALL']), quote_amount_decimals)
                message_values = {
                    'exchange': exchange,
                    'quantity': trades_size['ALL'],
                    'price_average': 0 if amount_sum['ALL'] == 0 else f"%.{price_decimals}f" % round(float((quote_amount / base_amount)), price_decimals),
                    'base_asset': base_asset,
                    'base_amount': f"%.{base_amount_decimals}f" % base_amount,
                    'base_amount_fee': f"%.{base_amount_decimals}f" % round(float(base_fee_sum['ALL']), base_amount_decimals),
                    'quote_asset': quote_asset,
                    'quote_amount': f"%.{quote_amount_decimals}f" % quote_amount,
                    'quote_amount_fee': f"%.{quote_amount_decimals}f" % round(float(quote_fee_sum['ALL']), quote_amount_decimals),
                }
                send_alert(alert_type='trades_sell_report_' + template, message_values=message_values, channel=channel)
            case 'strategy':
                strategies = {}
                basic_rules = await self.get_basic_rules()
                for rule in basic_rules:
                    for action in rule['actions']:
                        logging.info('------------------------1 %s', action)
                        if len(action.split('__')) == 3 and action.split('__')[0] == 'bot' and action.split('__')[1] == 'change_strategy':
                            strategy = action.split('__')[2]
                            logging.info('------------------------2 %s', action)
                            if strategy not in strategies:
                                if strategy not in amount_sum:
                                    amount_sum[strategy] = 0
                                if strategy not in base_fee_sum:
                                    base_fee_sum[strategy] = 0
                                if strategy not in price_by_amount_sum:
                                    price_by_amount_sum[strategy] = 0
                                if strategy not in quote_fee_sum:
                                    quote_fee_sum[strategy] = 0
                                if strategy not in trades_size:
                                    trades_size[strategy] = 0
                                base_amount = round(float(amount_sum[strategy]) - float(base_fee_sum[strategy]), base_amount_decimals)
                                quote_amount = round(float(price_by_amount_sum[strategy]) - float(quote_fee_sum[strategy]), quote_amount_decimals)
                                strategies[strategy] = {
                                    'quantity': trades_size[strategy],
                                    'price_average': 0 if amount_sum[strategy] == 0 else f"%.{price_decimals}f" % round(float((quote_amount / base_amount)), price_decimals),
                                    'base_asset': base_asset,
                                    'base_amount': f"%.{base_amount_decimals}f" % base_amount,
                                    'base_amount_fee': f"%.{base_amount_decimals}f" % round(float(base_fee_sum[strategy]), base_amount_decimals),
                                    'quote_asset': quote_asset,
                                    'quote_amount': f"%.{quote_amount_decimals}f" % quote_amount,
                                    'quote_amount_fee': f"%.{quote_amount_decimals}f" % round(float(quote_fee_sum[strategy]), quote_amount_decimals),
                                }
                logging.info('------------------------3 %s', strategies)
                message = ''
                for key in strategies:
                    price_str = f' at {str(strategies[key]["price_average"])}' if float(strategies[key]['price_average']) > 0 else ''
                    message += f'%0A  - {key} --> {str(strategies[key]["quantity"])} sell trades today{price_str}. Total sold amount is {str(strategies[key]["base_amount"])} {str(strategies[key]["base_asset"])} collecting {str(strategies[key]["quote_amount"])} {str(strategies[key]["quote_asset"])}'                    
                logging.info('------------------------4 %s', message)
                message_values = {
                    'exchange': exchange,
                    'message': message,
                }      
                logging.info('------------------------5 %s', message_values)          
                send_alert(alert_type='trades_sell_report_' + template, message_values=message_values, channel=channel)

    async def send_arbitrage_candidate_alert(self, channel: str, exchange_1: str, exchange_2: str, base_asset: str, quote_asset: str, price_buy_1: float, price_sell_2: float, depth: float, levels: int, arb_opportunity: float, profitability: float, profit: float):
        pair: str = base_asset + '-' + quote_asset
        await self.execute(exchange=exchange_1, base_asset=base_asset, quote_asset=quote_asset, name='NONE', attributes=())
        await self.execute(exchange=exchange_2, base_asset=base_asset, quote_asset=quote_asset, name='NONE', attributes=())
        price_decimals_1 = self.commons[exchange_1 + '__' + pair].price_decimals
        price_decimals_2 = self.commons[exchange_2 + '__' + pair].price_decimals
        send_alert(alert_type='arbitrage_candidate', message_values={
            'base_asset': base_asset,
            'quote_asset': quote_asset,
            'exchange_1': exchange_1,
            'exchange_2': exchange_2,
            'price_buy_1': round(price_buy_1, price_decimals_1),
            'price_sell_2': round(price_sell_2, price_decimals_2),
            'depth': round(depth, price_decimals_1),
            'levels': levels,
            'arb_opportunity': round(arb_opportunity, price_decimals_1),
            'profitability': round(profitability, 3),
            'profit': round(profit, price_decimals_1)
        }, channel=channel)
                                              
    async def execute(self, exchange: str, base_asset: str, quote_asset: str, name: str, attributes: tuple) -> dict[str, Any]:
        key: str = exchange + '__' + base_asset + '-' + quote_asset
        if not key in self.commons:
            commons = get_commons(exchange_or_connector=exchange, api_or_wallet=self.exchanges_apis[exchange], base_asset=base_asset, quote_asset=quote_asset)  
            if commons is None:
                await self.self_inactivate(reason='Exchange or market is not supported')
            self.commons[key] = commons
        if name == 'NONE':
            return {}
        return await getattr(self.commons[key], name)(*attributes)
    
    async def self_inactivate(self, reason: str) -> None:        
        with open('config.json', encoding='UTF-8') as f:
            config = json.load(f)
            with open('config.json', 'w', encoding='UTF-8') as f:
                config['active'] = False
                f.write(json.dumps(config))
                logging.info('========== INACTIVATING bot because %s ==========', reason)
                
    async def get_basic_rules(self) -> dict:
        with open('rules.json', encoding='UTF-8') as f:
            return json.load(f)    
        
    async def get_bot_rules(self) -> list:
        bot_rules = []
        for rule in self.rules:
            for actions in rule['actions']:
                if ('bot__change_status__restart' or 'bot__change_status__activate') in actions:
                    bot_rules.append(rule)
                    break
        return bot_rules
