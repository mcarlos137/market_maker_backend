from threading import Thread
import sys
import os
import logging
sys.path.append(os.getcwd())
from order_books.base import OrderBooks
from damexCommons.businesses.base import ExchangeCommons
from damexCommons.tools.exchange_db import ExchangeDB
from damexCommons.tools.connections import get_commons
from damexCommons.tools.damex_http_client import get_main_price


def run_order_books_thread(exchange: str, base_asset: str, quote_asset: str, commons: ExchangeCommons):
    tickers = OrderBooks(
        exchange=exchange, 
        base_asset=base_asset, 
        quote_asset=quote_asset, 
        commons=commons
    )
    tickers.run()
    
exchanges_included = ['coinstore', 'ascendex', 'tidex', 'mexc', 'bitmart']
    
exchange_db = ExchangeDB(db_connection='data_collector')
exchanges_info = exchange_db.fetch_exchanges_info_db()

for exchange in exchanges_info:
    if exchange not in exchanges_included:
        continue
    for market in exchanges_info[exchange]:
        try:
            base_asset = market.split('-')[0]
            quote_asset = market.split('-')[1]
            commons = get_commons(
                base_asset=base_asset,
                quote_asset=quote_asset,
                exchange_or_connector=exchange,
                api_or_wallet=exchange + '__' + 'main'
            )
            if commons is None:
                logging.error('commons does not exist %s %s', exchange, market)
                continue
        except Exception as e:
            logging.error('exception, %s', e)
            continue
        if exchanges_info[exchange][market]['data_collect']:
            t = Thread(target=run_order_books_thread, args=(exchange, base_asset, quote_asset, commons,))
            t.start()    
