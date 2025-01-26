import logging
import json
import sys
import os
sys.path.append(os.getcwd())
from period_data_type import PeriodDataType
from damexCommons.tools.utils import OPERATIONS_DATA_TYPES, PERIODS
from tools.utils import get_new_file_time

class OrderBooksPeriodDataType(PeriodDataType):
        
    def __init__(self, exchange: str, base_asset: str, quote_asset: str) -> None:
        PeriodDataType.__init__(
            self, 
            exchange=exchange, 
            base_asset=base_asset, 
            quote_asset=quote_asset, 
            operation='order_books',
        )
            
    def callback(self, src_path: str, data: dict) -> callable:
        try:
            file_name = src_path.split('/')[7]
            main_folder = src_path.replace(src_path.split('/')[7],'')
            file_time = int(file_name.split('.')[0])
            for period in PERIODS:
                for data_type in OPERATIONS_DATA_TYPES[self.operation]:
                    final_folder = main_folder + period + '/' + data_type
                    new_file_time = get_new_file_time(file_time, period)
                    final_file = final_folder + '/' + str(new_file_time) + '.json'
                    logging.info('final_file %s', final_file)
                    new_file_data = {'time': new_file_time, 'asks': data['asks'], 'bids': data['bids']}
                    if os.path.exists(final_file):
                        os.remove(final_file)                
                    with open(final_file, "w", encoding='UTF-8') as jsonFile:                                
                        json.dump(new_file_data, jsonFile)
                            
        except (Exception) as error:
            logging.error("Error while parsing data %s", error)
