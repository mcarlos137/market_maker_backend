from threading import Thread
import logging
import time
import sys
import os
import asyncio
from typing import Optional
sys.path.append(os.getcwd())
from current_values.base import CurrentValues
from damexCommons.businesses.base import ExchangeCommons
from damexCommons.tools.exchange_db import ExchangeDB
from damexCommons.tools.connections import get_commons
from damexCommons.tools.damex_http_client import get_main_price

wait_for_prices: bool = True
prices: dict[str, dict] = {}
exchanges_with_aux = ['ascendex'] 
exchanges_excluded = []

def run_current_values_thread(exchange: str, commons: ExchangeCommons, commons_aux: Optional[ExchangeCommons] = None):
    while wait_for_prices:
        time.sleep(5)
        continue
    current_values = CurrentValues(
        exchange=exchange, 
        prices=prices,
        commons=commons,
        commons_aux=commons_aux
    )
    current_values.run()
    
def run_prices_thread():
    while True:
        for market in prices:
            base_asset = market.split('-')[0]
            quote_asset = market.split('-')[1]
            main_price = asyncio.run(get_main_price(base_asset=base_asset, quote_asset=quote_asset, price_decimals=prices[market]['price_decimals']))
            if main_price > 0:
                prices[market]['price'] = main_price
        time.sleep(60)

exchange_db = ExchangeDB(db_connection='data_collector')
exchanges_info = exchange_db.fetch_exchanges_info_db()

for exchange in exchanges_info:
    if exchange in exchanges_excluded:
        continue
    for market in exchanges_info[exchange]:
        if market not in prices:
            prices[market] = {
                'price': 0,
                'price_decimals': exchanges_info[exchange][market]['price_decimals']
            }
    try:
        commons_aux = None
        commons = get_commons(
            base_asset='BASE',
            quote_asset='QUOTE',
            exchange_or_connector=exchange,
            api_or_wallet=exchange + '__' + 'main'
        )
        if exchange in exchanges_with_aux:
            commons_aux = get_commons(
                base_asset='BASE',
                quote_asset='QUOTE',
                exchange_or_connector=exchange,
                api_or_wallet=exchange + '__' + 'main_aux'
            )
        if commons is None or (exchanges_with_aux and commons_aux):
            logging.error('commons does not exist %s', exchange)
            continue
    except Exception as e:
        print('exception', e)
        continue
    
    t = Thread(target=run_current_values_thread, args=(exchange, commons, commons_aux))
    t.start()    

t = Thread(target=run_prices_thread)
t.start()    
wait_for_prices = False