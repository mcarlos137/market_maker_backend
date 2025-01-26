import logging
import asyncio
import time
from logging.handlers import RotatingFileHandler
import sys
import os
sys.path.append(os.getcwd())
from tools.utils import get_new_file_data_for_pnl_values_ticker, get_current_time
from period_data_type import PeriodDataType
from damexCommons.tools.exchange_db import ExchangeDB


class CurrentPnl:
        
    def __init__(self, exchange: str, base_asset: str, quote_asset: str, exchange_db: ExchangeDB) -> None:
        self.exchange = exchange
        self.base_asset = base_asset
        self.quote_asset = quote_asset
        self.operation = 'current_pnl'
        self.exchange_db = exchange_db
        
        logging.basicConfig(
            level=logging.INFO, 
            handlers=[
                RotatingFileHandler(f"{self.operation}_{self.exchange}_{self.base_asset}-{self.quote_asset}.log", mode='a', maxBytes=1024*1024*10, backupCount=10, encoding=None, delay=0),
                logging.StreamHandler()
            ],
            format="%(asctime)s %(levelname)s %(message)s"
        )
        
    @property
    def market(self):
        return self.base_asset + '-' + self.quote_asset    
        
    def run(self):
        #exchange_folder = BASE_PATH + '/exchange_files/' + self.exchange
        #if not os.path.exists(exchange_folder):
        #    os.makedirs(exchange_folder)
        #operation_exchange_folder = exchange_folder + '/' + self.operation
        #if not os.path.exists(operation_exchange_folder):
        #    os.makedirs(operation_exchange_folder)
        #market_operation_exchange_folder = operation_exchange_folder + '/' + self.market
        #if not os.path.exists(market_operation_exchange_folder):
        #    os.makedirs(market_operation_exchange_folder)
       
        while True:
            current_time = None
            if current_time is None:
                current_time = get_current_time()
            initial_time = current_time - (15 * 1000)
            logging.info('current_time %s', current_time)
            logging.info('initial_time %s', initial_time)
                        
            trades = asyncio.run(self.exchange_db.fetch_trades_db(
                exchanges=[self.exchange], 
                base_asset=self.base_asset,
                quote_asset=self.quote_asset,
                sides=[1, 2],
                order_timestamp='DESC',
                initial_timestamp=initial_time,
                final_timestamp=current_time,
                offset=0,
                )
            )
            
            logging.info('%s %s-%s trades -> %s', self.exchange, self.base_asset, self.quote_asset, trades)
            
            #f = open(market_operation_exchange_folder + '/' + str(current_time) + '.json', 'w+', encoding='UTF-8')
            #f.write(json.dumps(current_orders_data))
            #f.close()
            current_time = None
            time.sleep(15)
            
                    
class CurrentPnlPeriodDataType(PeriodDataType):
        
    def __init__(self, exchange: str, base_asset: str, quote_asset: str) -> None:
        PeriodDataType.__init__(
            self, 
            exchange=exchange, 
            base_asset=base_asset, 
            quote_asset=quote_asset, 
            operation='current_pnl',
            file_data_callback=get_new_file_data_for_pnl_values_ticker
        )
