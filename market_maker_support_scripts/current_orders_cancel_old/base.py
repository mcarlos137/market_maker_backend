import time
import logging
import asyncio
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional
from damexCommons.connectors.base import ExchangeCommons


class CurrentOrdersCancelOld:
    
    def __init__(self, exchange: str, base_asset: str, quote_asset, commons: ExchangeCommons, commons_aux: Optional[ExchangeCommons] = None):
        self.exchange = exchange
        self.base_asset = base_asset
        self.quote_asset = quote_asset
        self.operation = 'current_orders_cancel_old'
        self.commons = commons
        self.commons_aux = commons_aux
        
        logging.basicConfig(
            level=logging.INFO, 
            handlers=[
                RotatingFileHandler(f"{self.operation}_{self.exchange}_{self.base_asset}{self.quote_asset}.log", mode='a', maxBytes=1024*1024*10, backupCount=10, encoding=None, delay=0),
                logging.StreamHandler()
            ],
            format="%(asctime)s %(levelname)s %(message)s"
        )
        
    def run(self):
        while True:
            try:
                current_timestamp = int(datetime.now().timestamp() * 1000)
                commons_list = [self.commons]
                if self.commons_aux is not None:
                    commons_list.append(self.commons_aux)
                for commons in commons_list:
                    active_orders: list[dict] = asyncio.run(commons.fetch_active_orders())
                    logging.info('active_orders %s %s-%s aux %s -> len %s', self.exchange, self.base_asset, self.quote_asset, commons != self.commons, len(active_orders))
                    for active_order in active_orders:
                        order_timestamp = active_order['timestamp']
                        if order_timestamp < 946684800000:
                            order_timestamp *= 1000
                        order_id = None
                        if 'id' in active_order:
                            order_id = active_order['id']
                        elif 'ordId' in active_order:
                            order_id = active_order['ordId']
                        else:
                            raise Exception('order id was not found to %s %s-%s' % (self.exchange, self.base_asset, self.quote_asset))
                        if (current_timestamp - order_timestamp) > (12 * 60 * 1000):
                            time.sleep(1)
                            logging.info('cancelling old active order %s %s %s -> %s', self.exchange, self.base_asset, self.quote_asset, active_order)
                            asyncio.run(self.commons.cancel_limit_order(order_id=order_id))
                    time.sleep(5)
            except Exception as e:
                logging.error('%s %s-%s -> exception %s', self.exchange, self.base_asset, self.quote_asset, e)
                time.sleep(5)
            time.sleep(30)
