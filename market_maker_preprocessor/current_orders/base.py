import logging
import asyncio
import time
import json
from logging.handlers import RotatingFileHandler
import sys
import os
sys.path.append(os.getcwd())
from period_data_type import PeriodDataType
from tools.utils import get_current_time, get_new_file_time, process_data
from damexCommons.tools.exchange_db import ExchangeDB
from damexCommons.tools.utils import BASE_PATH, PERIODS, OPERATIONS_DATA_TYPES


class CurrentOrders:
        
    def __init__(self, exchange: str, base_asset: str, quote_asset: str, exchange_db: ExchangeDB) -> None:
        self.exchange = exchange
        self.base_asset = base_asset
        self.quote_asset = quote_asset
        self.operation = 'current_orders'
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
        exchange_folder = BASE_PATH + '/exchange_files/' + self.exchange
        if not os.path.exists(exchange_folder):
            os.makedirs(exchange_folder)
        operation_exchange_folder = exchange_folder + '/' + self.operation
        if not os.path.exists(operation_exchange_folder):
            os.makedirs(operation_exchange_folder)
        market_operation_exchange_folder = operation_exchange_folder + '/' + self.market
        if not os.path.exists(market_operation_exchange_folder):
            os.makedirs(market_operation_exchange_folder)
       
        while True:
            current_time = None
            if current_time is None:
                current_time = get_current_time()
            initial_time = current_time - (15 * 1000)
            logging.info('current_time %s', current_time)
            logging.info('initial_time %s', initial_time)
            
            data: list[dict] = []
            order_book = asyncio.run(self.exchange_db.get_order_book_db(
                base_asset=self.base_asset, 
                quote_asset=self.quote_asset, 
                size=100, 
                exchange=self.exchange
                )
            )
            #logging.info('%s %s-%s order_book -> %s', self.exchange, self.base_asset, self.quote_asset, order_book)
            for order in order_book['asks']:
                data.append({
                    'id': '',
                    'order_side': 'ASK',
                    'amount': float(order[1]),
                    'price': float(order[0])
                })
            #logging.info('%s %s-%s data_1 -> %s', self.exchange, self.base_asset, self.quote_asset, data)
            trades = asyncio.run(self.exchange_db.fetch_trades_db(
                exchanges=[self.exchange], 
                base_asset=self.base_asset,
                quote_asset=self.quote_asset,
                sides=[1, 2],
                order_timestamp='DESC',
                initial_timestamp=initial_time,
                final_timestamp=current_time,
                offset=0,
                bot_types=['maker']
                )
            )
            #logging.info('%s %s-%s trades -> %s', self.exchange, self.base_asset, self.quote_asset, trades)
            for trade in trades:
                data.append({
                    'id': '',
                    'order_side': trade.side.name,
                    'amount': trade.amount,
                    'price': trade.price
                })
            #logging.info('%s %s-%s data_2 -> %s', self.exchange, self.base_asset, self.quote_asset, data)
            current_orders_data = {
                'time': current_time,
                'data': data
            }
            logging.info('%s %s-%s current_orders_data -> %s', self.exchange, self.base_asset, self.quote_asset, current_orders_data)
            f = open(market_operation_exchange_folder + '/' + str(current_time) + '.json', 'w+', encoding='UTF-8')
            f.write(json.dumps(current_orders_data))
            f.close()
            current_time = None
            time.sleep(15)
            
                    
class CurrentOrdersPeriodDataType(PeriodDataType):
        
    def __init__(self, exchange: str, base_asset: str, quote_asset: str) -> None:
        PeriodDataType.__init__(
            self, 
            exchange=exchange, 
            base_asset=base_asset, 
            quote_asset=quote_asset, 
            operation='current_orders',
        )
            
    def callback(self, src_path: str, data: dict) -> callable:
        file_name = src_path.split('/')[7] #5
        main_folder = src_path.replace(src_path.split('/')[7],'') #5
        file_time = int(file_name.split('.')[0]) #0
        for period in PERIODS:
            for operation in OPERATIONS_DATA_TYPES:
                if self.operation not in operation:
                    continue
                main_folder = main_folder.replace(main_folder.split('/')[5], operation) #3
                for data_type in OPERATIONS_DATA_TYPES[operation]:
                    final_folder = main_folder + period + '/' + data_type
                    new_file_time = get_new_file_time(file_time, period)
                    final_file = final_folder + '/' + str(new_file_time) + '.json'
                    data['time'] = new_file_time
                    new_file_data =  get_new_file_data(data, data_type, operation, final_file, PERIODS[period])
                    logging.info('-----------> %s %s %s %s %s', self.exchange, period, data_type, new_file_data['time'], new_file_data['values'])
                    if os.path.exists(final_file):
                        os.remove(final_file)        
                    with open(final_file, "w", encoding='UTF-8') as jsonFile:                                
                        json.dump(new_file_data, jsonFile)
                    
        
def get_new_file_data(data, data_type, operation, final_file, period_in_minutes):
    # write code
    attribute = None
    match(operation):
        case 'current_orders_count':
            attribute = 'count'
        case 'current_orders_amounts':
            attribute = 'amount'
        case 'current_orders_mid_prices':
            attribute = 'price'
    match(data_type):
        # =======SNAP CASE=======
        case 'snap':
            new_data = {
                'time': data['time']
            }
            return process_data(new_data, data['data'], operation, data_type, period_in_minutes, attribute)

        # =======INCR CASE=======
        # =======AVG CASE=======
        case 'incr' | 'avg':
            if os.path.exists(final_file):
                new_data = {
                    'time': data['time'],
                    'values': [], 
                }
                with open(final_file, 'r', encoding='UTF-8') as p:
                    previous_data = json.load(p)
                    new_data_data = previous_data['data']
                    for value in data['data']:
                        if value in new_data_data:
                            continue
                        new_data_data.append(value)
                new_data['data'] = new_data_data
                return process_data(new_data, new_data['data'], operation, data_type, period_in_minutes, attribute)
            new_data = {
                'time': data['time'],
                'data': data['data']
            }
            return process_data(new_data, data['data'], operation, data_type, period_in_minutes, attribute)
