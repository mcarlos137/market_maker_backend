import pika
import time
import logging
import json
from damexCommons.connectors.base import ExchangeCommons
from damexCommons.connectors.base import ExchangeWSSCommons
import sys
import os
sys.path.append(os.getcwd())
from wss import Wss
from damexCommons.tools.utils import add_data_exchange_file


class OrderBooks(Wss):
        
    def __init__(self, exchange: str, base_asset: str, quote_asset: str, commons: ExchangeCommons | ExchangeWSSCommons) -> None:
        Wss.__init__(
            self,
            exchange=exchange,
            base_asset=base_asset,
            quote_asset=quote_asset,
            operation='order_books',
            wss_object='order_book',
            commons=commons
        )
        self.queue_connection = pika.BlockingConnection(pika.ConnectionParameters('market_maker_rabbitmq'))
        self.queue_channel = self.queue_connection.channel()
        self.queue_channel.queue_declare(queue='%s.%s.%s-%s' % ('order_book', exchange, base_asset, quote_asset), arguments={'x-max-length': 1})
        self.queue_channel.queue_bind(queue='%s.%s.%s-%s' % ('order_book', exchange, base_asset, quote_asset), exchange='market_maker_backend', routing_key='%s.%s.%s-%s' % ('order_book', exchange, base_asset, quote_asset))       
                
    async def data_parser_callback(self, exchange: str, base_asset: str, quote_asset: str, data: dict) -> dict:
        current_time = int(time.time() * 1e3)
        if len(data) == 0:
            return
        logging.info('===============> %s %s-%s %s %s', exchange, base_asset, quote_asset, data, current_time)
                
        self.queue_channel.basic_publish(exchange='market_maker_backend',
            routing_key='order_book.%s.%s-%s' % (exchange, base_asset, quote_asset),
            body=json.dumps({'time': current_time, 'exchange': exchange, 'base_asset': base_asset, 'quote_asset': quote_asset, 'data': data})
        )
                
        #add_data_exchange_file(file_name=(str(current_time) + '.json'), data=data, exchange=self.exchange, operation=self.operation, market=self.market)
