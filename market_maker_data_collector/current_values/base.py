import time
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional
from damexCommons.connectors.base import ExchangeCommons
from damexCommons.tools.utils import add_data_exchange_file


class CurrentValues:
        
    def __init__(self, exchange: str, prices: dict[str, dict], commons: ExchangeCommons, commons_aux: Optional[ExchangeCommons] = None) -> None:
        self.exchange = exchange
        self.prices = prices
        self.operation = 'current_values'
        self.commons = commons
        self.commons_aux = commons_aux
        
        logging.basicConfig(
            level=logging.INFO, 
            handlers=[
                RotatingFileHandler(f"{self.operation}_{self.exchange}.log", mode='a', maxBytes=1024*1024*10, backupCount=10, encoding=None, delay=0),
                logging.StreamHandler()
            ],
            format="%(asctime)s %(levelname)s %(message)s"
        )
        
    async def data_parser(self, balance: dict, current_time: int, balance_aux: Optional[dict] = None) -> dict:
        values = []
        assets = set()
        for b in balance:
            assets.add(b)
        if balance_aux is not None:
            for b in balance:
                assets.add(b)
        for asset in assets:
            if asset in balance:
               amount = float(balance[asset]['total'])
            if balance_aux is not None and asset in balance_aux:
                amount += float(balance_aux[asset]['total'])
            values.append({
                'currency': asset,
                'amount': amount
            }) 
            if asset != 'USDT':
                pair = asset + '-USDT'
                if pair not in self.prices:
                    continue
                values.append({
                    'currency': b + '__USDT',
                    'amount': float(self.prices[pair]['price']) * amount
                })                   
        data = {
            'time': current_time,
            'values': values
        }
        return data
    
    def run(self):
        while True:
            current_time = int(datetime.now().replace(second=0, microsecond=0).timestamp() * 1000)
            balance = asyncio.run(self.commons.fetch_balance())
            logging.info('==================> %s %s', self.exchange, balance)
            if self.commons_aux is not None:
                balance_aux = asyncio.run(self.commons_aux.fetch_balance())
                data = asyncio.run(self.data_parser(balance=balance, current_time=current_time, balance_aux=balance_aux))
            else:
                data = asyncio.run(self.data_parser(balance=balance, current_time=current_time))
            add_data_exchange_file(file_name=(str(current_time) + '.json'), data=data, exchange=self.exchange, operation=self.operation, market='NONE')
            time.sleep(60)
