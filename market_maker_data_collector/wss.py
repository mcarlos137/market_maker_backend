import time
import asyncio
import logging
from abc import abstractmethod
from logging.handlers import RotatingFileHandler
from damexCommons.connectors.base import ExchangeCommons
from damexCommons.connectors.base import ExchangeWSSCommons


class Wss:

    def __init__(self, exchange: str, base_asset: str, quote_asset: str, operation: str, wss_object: str, commons: ExchangeCommons | ExchangeWSSCommons) -> None:
        self.exchange = exchange
        self.base_asset = base_asset
        self.quote_asset = quote_asset
        self.operation = operation
        self.wss_object = wss_object
        self.commons = commons
        self.stop_ws = {}
        
        logging.basicConfig(
            level=logging.INFO, 
            handlers=[
                RotatingFileHandler(f"{self.operation}.log", mode='a', maxBytes=1024*1024*10, backupCount=10, encoding=None, delay=0),
                logging.StreamHandler()
            ],
            format="%(asctime)s %(levelname)s %(message)s"
        )
        
    @property
    def market(self) -> str:
        return self.base_asset + '-' + self.quote_asset
        
    @abstractmethod
    async def data_parser_callback(self, exchange: str, base_asset: str, quote_asset: str, data: dict) -> dict:
        raise NotImplementedError
    
    def run(self):
        while True:
            thread_id = self.exchange + '__' + self.market
            self.stop_ws[thread_id] = False   
            asyncio.run(self.commons.run_wss(base_asset=self.base_asset, quote_asset=self.quote_asset, wss_object=self.wss_object, stop_wss=self.stop_ws, callback=self.data_parser_callback))
            time.sleep(3)
            logging.info('restarting %s thread %s %s %s', self.operation, self.exchange, self.base_asset, self.quote_asset)
