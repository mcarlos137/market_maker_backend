import os
import logging
from logging.handlers import RotatingFileHandler
import sys
sys.path.append(os.getcwd())
from watcher import Watcher
from damexCommons.tools.utils import BASE_PATH

PERIODS = ['1m', '5m', '15m', '30m', '1h', '4h', '12h', '1D', '5D', '15D', '30D']
METRICS = ['count', 'elapsed_time', ]

class ArbitrageOpportunitiesPeriod:
    
    def __init__(self) -> None:
        self.operation = 'arbitrage_opportunities_period'
        self.folders_to_watch = [BASE_PATH + '/arbitrage_opportunities/simple', BASE_PATH + '/arbitrage_opportunities/triple']
            
        logging.basicConfig(
            level=logging.INFO, 
            handlers=[
                RotatingFileHandler(f"{self.operation}.log", mode='a', maxBytes=1024*1024*10, backupCount=10, encoding=None, delay=0),
                logging.StreamHandler()
            ],
            format="%(asctime)s %(levelname)s %(message)s"
        )    

    def run(self):
        logging.info('=========================================== %s' , self.folders_to_watch)
        for folder_to_watch in self.folders_to_watch:
            for period in PERIODS:
                if not os.path.exists('%s/%s' % (folder_to_watch, period)):
                    os.makedirs('%s/%s' % (folder_to_watch, period))
                for metric in METRICS:
                    if not os.path.exists('%s/%s/%s' % (folder_to_watch, period, metric)):
                        os.makedirs('%s/%s/%s' % (folder_to_watch, period, metric))
        watcher = Watcher(folders_to_watch=self.folders_to_watch, callback=self.callback)
        watcher.run()
    
    def callback(self, src_path: str, data: dict) -> callable:
        try:
            logging.info('----------> %s %s', src_path, data)
        except (Exception) as error:
            logging.error("Error while parsing data %s", error)
    
    
arbitrage_opportunities_period = ArbitrageOpportunitiesPeriod()
arbitrage_opportunities_period.run()
