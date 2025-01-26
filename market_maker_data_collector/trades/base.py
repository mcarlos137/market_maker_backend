import time
import logging
from damexCommons.connectors.base import ExchangeCommons
from damexCommons.connectors.base import ExchangeWSSCommons
import sys
import os
sys.path.append(os.getcwd())
from wss import Wss
from damexCommons.tools.utils import add_data_exchange_file, add_to_info


class Trades(Wss):
        
    def __init__(self, exchange: str, base_asset: str, quote_asset: str, commons: ExchangeCommons | ExchangeWSSCommons) -> None:
        Wss.__init__(
            self,
            exchange=exchange,
            base_asset=base_asset,
            quote_asset=quote_asset,
            operation='trades',
            wss_object='trade',
            commons=commons
        )
                
    async def data_parser_callback(self, exchange: str, base_asset: str, quote_asset: str, data: dict) -> dict:
        current_time = int(time.time() * 1e3)
        if data is None or len(data) == 0:
            return
        logging.info('====================> %s %s-%s %s %s', exchange, base_asset, quote_asset, data, current_time)
        short_trade = {'timestamp': data['time'], 'price': data['price'], 'amount': data['amount'], 'side': data['side']}
        logging.info('short_trade=====================================================> %s', short_trade)
        
        add_to_info(key='last_trade_price', value=data['price'], action='replace', exchange=self.exchange, operation=self.operation, market=self.market)
        add_to_info(key='last_trades', value=short_trade, action='add', exchange=self.exchange, operation=self.operation, market=self.market)
        add_data_exchange_file(file_name=(str(current_time) + '.json') ,data=data, exchange=self.exchange, operation=self.operation, market=self.market)
