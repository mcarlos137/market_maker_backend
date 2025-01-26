import time
from threading import Event, Thread
import logging
import random
import os
import sys
sys.path.append(os.getcwd())
from vol.base import VolBotBase, VolBot


class VolBotCLOB(VolBot):
    
    def __init__(self, vol_bot_base: VolBotBase) -> None:
        super().__init__(vol_bot_base=vol_bot_base)
        
    async def start(self) -> None:
        await self.refresh_strategy_and_target()
        t_1 = Thread(target=self.strategy_check_thread, args=(Event(),))
        t_1.start()       
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
                price = 1
                if self.current_amount <= self.strategy['target_amount']:
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