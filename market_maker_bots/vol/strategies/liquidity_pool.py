import time
from threading import Event, Thread
import logging
import random
import asyncio
import os
import sys
sys.path.append(os.getcwd())
from vol.base import VolBotBase, VolBot
from damexCommons.base import TradeSide, Trade
from damexCommons.tools.damex_http_client import get_main_price


class VolBotLiquidityPool(VolBot):
    
    def __init__(self, vol_bot_base: VolBotBase) -> None:
        super().__init__(vol_bot_base=vol_bot_base)
    
    
    async def start(self) -> None:
        await self.refresh_strategy_and_target()
        t_1 = Thread(target=self.strategy_check_thread, args=(Event(),))
        t_1.start()       
        #t_2 = Thread(target=self.inactivate_check_thread, args=(Event(),))
        #t_2.start()
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
                # target_amount lower_order_amount higher_order_amount lower_order_time
                logging.info('========== START strategy check thread ==========')  
                if self.current_amount <= self.strategy['target_amount']:
                    balance = asyncio.run(self.execute(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, name='fetch_balance', attributes=()))
                    total_base_amount: float = balance[self.base_asset]['total']
                    total_quote_amount: float = balance[self.quote_asset]['total']
                    main_price = asyncio.run(get_main_price(base_asset=self.base_asset, quote_asset=self.quote_asset, price_decimals=self.commons[self.exchange + '__' + self.pair].price_decimals))
                    trade_side: TradeSide = TradeSide.BUY if random.randint(0, 1) == 1 else TradeSide.SELL
                    if total_base_amount < 0.02 and self.base_asset == 'SOL':
                        trade_side = TradeSide.BUY
                    elif total_quote_amount < 20 and self.quote_asset == 'USDC':
                        trade_side = TradeSide.SELL
                                        
                    base_amount: float = round(random.uniform(self.strategy['lower_order_amount'], self.strategy['higher_order_amount']), self.commons[self.exchange + '__' + self.pair].base_amount_decimals)
                    if trade_side == TradeSide.BUY:
                        amount = base_amount * main_price   
                    else:
                        amount = base_amount            
                    swap_prices = asyncio.run(self.execute(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, name='fetch_swap_prices', attributes=(trade_side, amount,)))                    
                    price = swap_prices['executionPrice']
                            
                    threshold_percent_around_main_price = self.strategy['threshold_percent_around_main_price']
                    logging.info('main_price %s', main_price)
                    logging.info('trade_side %s', trade_side)
                    logging.info('base_amount %s', base_amount)
                    logging.info('amount %s', amount)
                    logging.info('price %s', price)
                    logging.info('top threshold %s', price * (100 + threshold_percent_around_main_price) / 100)
                    logging.info('bottom threshold %s', price * (100 - threshold_percent_around_main_price) / 100)                    
                    
                    if price * (100 + threshold_percent_around_main_price) / 100 < main_price or price * (100 - threshold_percent_around_main_price) / 100 > main_price:
                        logging.info('swap price is out of threshold percent from main price')
                        time.sleep(10)
                        continue
                    execute: bool = False
                         
                    if execute:
                        send_swap = asyncio.run(self.execute(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, name='send_swap_transaction', attributes=(trade_side, amount, price,)))
                        logging.info('send swap %s', send_swap)
                        
                        if not 'txid' in send_swap:
                            logging.info('send swap failed')
                            time.sleep(10)
                            continue
                        txid: str = send_swap['txid']
                        if txid == '1111111111111111111111111111111111111111111111111111111111111111':
                            logging.info('simulate failed by %s', txid)
                            time.sleep(10)
                            continue
                    
                        trade_timestamp = int(time.time() * 1e3)      
                        trade = Trade(bot_id=self.bot_id, strategy_id=self.strategy['id'], base_asset=self.base_asset, quote_asset=self.quote_asset, timestamp=trade_timestamp, order_id='NONE', side=trade_side, price=price, amount=base_amount, fee={}, exchange_id=txid, exchange=self.exchange)
                        asyncio.run(self.bot_db.create_trade_db(trade=trade))
                        logging.info('trade created %s', trade)
                                                                 
                    else: 
                        simulate_swap = asyncio.run(self.execute(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, name='simulate_swap_transaction', attributes=(trade_side, amount,)))
                        if simulate_swap['sim']['value']['err'] != None:
                            logging.info('swap simulation failed %s', simulate_swap["sim"]["value"])
                        else:
                            logging.info('swap simulation OK %s', simulate_swap["sim"]["value"])
                    self.current_amount += base_amount                    
                    upper_limit_time = int((86400 * 2 / (self.strategy['target_amount'] / (price * (self.strategy['lower_order_amount'] + self.strategy['higher_order_amount']) / 2))) - self.strategy['lower_order_time'])
                    logging.info('upper_limit_time %s', upper_limit_time)
                    logging.info('Current = %s', self.current_amount)
                    #logging.info(f"24h estimation = {(86400 * self.current_amount) / int((int(time.time() * 1000) - self.initial_timestamp) / 1000)}")
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
                
    
                 