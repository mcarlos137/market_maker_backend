import json
import os
from ..watchers_wss.trades import WatcherWssTrades
from ..utils import DATA_FOLDER, DATA_OLD_FOLDER
from .base import ConsumerBase


WSS_ROUTE = 'trades'
ALLOWED_OPERATIONS = ['fetch']

watcher_wss_trades = None

class ConsumerTrades(ConsumerBase):
    
    def __init__(self, *args, **kwargs):
        kwargs['wss_route'] = WSS_ROUTE
        kwargs['allowed_operations'] = ALLOWED_OPERATIONS
        global watcher_wss_trades
        if watcher_wss_trades is None:
            watcher_wss_trades = WatcherWssTrades()
            watcher_wss_trades.run()
            print('watcher wss %s initiated' % (WSS_ROUTE))
        kwargs['add_old_data_callback'] = self.add_old_data_callback
        super().__init__(*args, **kwargs)
                
        
    def add_old_data_callback(self, *args, **kwargs):
        market = kwargs['market']
        if market == 'DAMEX-USDT':
            exchanges = ['APP']
            exchanges.extend(['bitmart', 'coinstore', 'mexc', 'tidex', 'ascendex'])
        elif market == 'HOT-USDT':
            exchanges = ['binance']
        trades_timestamp = {}
        for exchange in exchanges:
            info_file = '%s/%s/%s/%s/%s' % (DATA_FOLDER, exchange, 'trades', market, 'info.json')
            if not os.path.exists(info_file):
                continue
            try:
                info = json.loads(open(info_file, 'r', encoding='UTF-8').read())
            except Exception as e:
                print('exception', e)
                continue
            last_file_name = info['last_file_name']
            trade_file = '%s/%s/%s/%s/%s' % (DATA_FOLDER, exchange, 'trades', market, last_file_name)
            if not os.path.exists(trade_file):
                trade_file = '%s/%s/%s/%s/%s' % (DATA_OLD_FOLDER, exchange, 'trades', market, last_file_name)
            if not os.path.exists(trade_file):
                continue
            trade = json.loads(open(trade_file, 'r', encoding='UTF-8').read())
            timestamp = trade['timestamp']
            trades_timestamp[timestamp] = trade
        
        trades_timestamp = sort(trades_timestamp, reverse=True)
        trades = []    
        for timestamp in trades_timestamp:
            trades.append(trades_timestamp[timestamp])
        
        return trades

                
def sort(object: dict={}, reverse: bool=False) -> dict: 
    sorted_object = {}
    for i in sorted(object.keys(), key=float, reverse=reverse):
        sorted_object[i] = object[i]
    return sorted_object                
