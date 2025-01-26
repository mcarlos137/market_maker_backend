import json
import os
import time
from datetime import datetime
from damexCommons.tools.utils import get_period_datetime, PERIODS
from ..utils import DATA_FOLDER, DATA_OLD_FOLDER, ROUTE_OPERATIONS
from ..watchers_wss.current_spread import WatcherWssCurrentSpread
from .base import ConsumerBase

WSS_ROUTE = 'current_spread'
ALLOWED_OPERATIONS = ['get']

watcher_wss_current_spread = None

class ConsumerCurrentSpread(ConsumerBase):
    
    def __init__(self, *args, **kwargs):
        kwargs['wss_route'] = WSS_ROUTE
        kwargs['allowed_operations'] = ALLOWED_OPERATIONS
        global watcher_wss_current_spread
        if watcher_wss_current_spread is None:
            watcher_wss_current_spread = WatcherWssCurrentSpread()
            watcher_wss_current_spread.run()
            print('watcher wss %s initiated' % (WSS_ROUTE))
        kwargs['add_old_data_callback'] = self.add_old_data_callback
        super().__init__(*args, **kwargs)
                                
    def add_old_data_callback(self, *args, **kwargs):
        operation = kwargs['operation']
        exchange = kwargs['exchange']
        market = kwargs['market']
        period = kwargs['period']
        dataset = kwargs['dataset']
        current_time = kwargs['current_time']
        size = int(kwargs['size'])
        if current_time is None:
            current_time = int(time.time() * 1000)
        final_old_data = []
        data_folder = '%s/%s/%s/%s' % (DATA_FOLDER, exchange,ROUTE_OPERATIONS[WSS_ROUTE][operation]['folders'][0], market)
        data_folder_old = '%s/%s/%s/%s' % (DATA_OLD_FOLDER, exchange, ROUTE_OPERATIONS[WSS_ROUTE][operation]['folders'][0], market)
        current_datetime = datetime.fromtimestamp(int((current_time / 1e3) - (60)))
        period_datetime = get_period_datetime(current_datetime, period)
        i = 0
        while i < size:
            period_time = int(period_datetime.timestamp() * 1000 - (PERIODS[period] * 60 * 1000 * i))
            data_file = '%s/%s/%s/%s' % (data_folder, period, dataset, str(period_time) + '.json')
            data_file_old = '%s/%s/%s/%s' % (data_folder_old, period, dataset, str(period_time) + '.json')
            old_data = None
            if os.path.exists(data_file):
                old_data = json.loads(open(data_file, 'r', encoding='UTF-8').read())
            elif os.path.exists(data_file_old):
                old_data = json.loads(open(data_file_old, 'r', encoding='UTF-8').read())
            if old_data is None:
                final_old_data.insert(0, {
                    'time': period_time, 'values': []
                })
                i = i + 1
                continue
            if 'time' in old_data and 'values' in old_data:
                final_old_data.insert(0, {
                    'time': old_data['time'],
                    'values': old_data['values']
                })
                        
            i = i + 1

        return final_old_data