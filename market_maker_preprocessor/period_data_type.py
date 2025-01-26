import logging
import os
import json
from logging.handlers import RotatingFileHandler
from watcher import Watcher
from damexCommons.tools.utils import BASE_PATH, OPERATIONS_DATA_TYPES, PERIODS
from tools.utils import get_new_file_time
                    
class PeriodDataType:
        
    def __init__(self, exchange: str, base_asset: str, quote_asset: str, operation: str, file_data_callback: callable = None) -> None:
        self.exchange = exchange
        self.base_asset = base_asset
        self.quote_asset = quote_asset
        self.operation = operation
        self.file_data_callback = file_data_callback
        
        logging.basicConfig(
            level=logging.INFO, 
            handlers=[
                RotatingFileHandler(f"{self.operation + '_period_data_type'}_{self.exchange}_{self.market}.log", mode='a', maxBytes=1024*1024*10, backupCount=10, encoding=None, delay=0),
                logging.StreamHandler()
            ],
            format="%(asctime)s %(levelname)s %(message)s"
        )
        
    @property
    def market(self):
        if self.operation == 'current_values':
            return 'NONE'
        return self.base_asset + '-' + self.quote_asset
    
    def run(self):
        folder_to_watch = BASE_PATH + '/exchange_files/' + self.exchange + '/' + self.operation + '/' + self.market
        logging.info('=========================================== %s' , folder_to_watch)
        for period in PERIODS:
            if not os.path.exists('%s/%s' % (folder_to_watch, period)):
                os.makedirs('%s/%s' % (folder_to_watch, period))
            for data_type in OPERATIONS_DATA_TYPES[self.operation]:
                if not os.path.exists('%s/%s/%s' % (folder_to_watch, period, data_type)):
                    os.makedirs('%s/%s/%s' % (folder_to_watch, period, data_type))
        watcher = Watcher(folders_to_watch=[folder_to_watch], callback=self.callback)
        watcher.run()
        
    def callback(self, src_path: str, data: dict) -> callable:
        try:
            operation = src_path.split('/')[5]
            file_name = src_path.split('/')[7]
            main_folder = src_path.replace(src_path.split('/')[7],'')
            file_time = int(file_name.split('.')[0])
            for period in PERIODS:
                for data_type in OPERATIONS_DATA_TYPES[operation]:
                    final_folder = main_folder + period + '/' + data_type
                    new_file_time = get_new_file_time(file_time, period)
                    final_file = final_folder + '/' + str(new_file_time) + '.json'
                    data['time'] = new_file_time
                    new_file_data = self.file_data_callback(data, data_type, operation, final_file)
                    logging.info('----------> %s %s', self.exchange, new_file_data)
                    if os.path.exists(final_file):
                        os.remove(final_file)        
                    with open(final_file, "w", encoding='UTF-8') as jsonFile:                                
                        json.dump(new_file_data, jsonFile)
        except (Exception) as error:
            logging.error("Error while parsing data %s", error)
        