import time
from threading import Thread, Event
import logging
import os
import sys
sys.path.append(os.getcwd())
from damexCommons.connectors.base import ExchangeCommons
from damexCommons.businesses.base import SimpleBusiness
from damexCommons.tools.dbs import get_bot_db


class TurnBotBase:
    
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
        

class TurnBot(SimpleBusiness):
    
    def __init__(self, turn_bot_base: TurnBotBase) -> None:
        super().__init__(
            bot_id=turn_bot_base.bot_id,
            bot_type=turn_bot_base.bot_type,
            active=turn_bot_base.active,
            bot_db=get_bot_db(db_connection='bot', bot_type='turn'),
            commons=turn_bot_base.commons,
            exchange=turn_bot_base.exchange, 
            base_asset=turn_bot_base.base_asset,
            quote_asset=turn_bot_base.quote_asset,
            tick_time=turn_bot_base.tick_time,
            )
                                                                                         
                
    async def start(self) -> None:
        #balance = await self.execute(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, name='fetch_balance', attributes=())
        #self.balance_1h_start = {self.base_asset: float(balance[self.base_asset]['total']), self.quote_asset: float(balance[self.quote_asset]['total'])}
        #self.balance_1h_timestamp = int(time.time() * 1e3)
        await self.refresh_strategy_and_target()
        t_1 = Thread(target=self.strategy_check_thread, args=(Event(),))
        t_1.start()                            
        t_2 = Thread(target=self.orders_check_thread, args=(Event(),))
        t_2.start()
        #t_3 = Thread(target=self.balance_1h_check_thread, args=(Event(),))
        #t_3.start() 
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
                
                logging.info('========== FINISH strategy check thread ========== %s', self.strategy["id"]) 
                
                time.sleep(self.tick_time)
            except Exception as e:
                logging.error('strategy check thread %s', e)
                time.sleep(1)
                
    async def refresh_orders(self, sides: list[str]) -> None:
        pass
                                                             