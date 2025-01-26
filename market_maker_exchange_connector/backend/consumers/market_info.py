from ..watchers_wss.market_info import WatcherWssMarketInfo
from .base import ConsumerBase


WSS_ROUTE = 'market_info'
ALLOWED_OPERATIONS = ['get']

watcher_wss_market_info = None

class ConsumerMarketInfo(ConsumerBase):
    
    def __init__(self, *args, **kwargs):
        kwargs['wss_route'] = WSS_ROUTE
        kwargs['allowed_operations'] = ALLOWED_OPERATIONS
        global watcher_wss_market_info
        if watcher_wss_market_info is None:
            watcher_wss_market_info = WatcherWssMarketInfo()
            watcher_wss_market_info.run()
            print('watcher wss %s initiated' % (WSS_ROUTE))
        kwargs['add_old_data_callback'] = self.add_old_data_callback
        super().__init__(*args, **kwargs)
                
    def add_old_data_callback(self, *args, **kwargs):
        return []