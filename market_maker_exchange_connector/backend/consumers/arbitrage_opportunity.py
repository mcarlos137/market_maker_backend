from ..watchers_wss.arbitrage_opppotunity import WatcherWssArbitrageOpportunities
from ..rabbitmq_wss.arbitrage_opppotunity import RabbitmqWssArbitrageOpportunities

from .base import ConsumerBase


WSS_ROUTE = 'arbitrage_opportunities'
ALLOWED_OPERATIONS = ['fetch']

watcher_wss_arbitrage_opportunities = None
rabbitmq_wss_arbitrage_opportunities = None

class ConsumerArbitrageOpportunities(ConsumerBase):
    
    def __init__(self, *args, **kwargs):
        kwargs['wss_route'] = WSS_ROUTE
        kwargs['allowed_operations'] = ALLOWED_OPERATIONS
        #global watcher_wss_arbitrage_opportunities
        #if watcher_wss_arbitrage_opportunities is None:
        #    watcher_wss_arbitrage_opportunities = WatcherWssArbitrageOpportunities()
        #    watcher_wss_arbitrage_opportunities.run()
        #    print('watcher wss %s initiated' % (WSS_ROUTE))
        global rabbitmq_wss_arbitrage_opportunities
        if rabbitmq_wss_arbitrage_opportunities is None:
            rabbitmq_wss_arbitrage_opportunities = RabbitmqWssArbitrageOpportunities()
            rabbitmq_wss_arbitrage_opportunities.run()
            print('rabbitmq wss %s initiated' % (WSS_ROUTE))
        kwargs['add_old_data_callback'] = self.add_old_data_callback
        super().__init__(*args, **kwargs)
                
    def add_old_data_callback(self, *args, **kwargs):
        return []