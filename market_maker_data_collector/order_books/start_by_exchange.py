from threading import Thread
import sys
import os
import logging
import time
sys.path.append(os.getcwd())
from order_books.base import OrderBooks
from damexCommons.businesses.base import ExchangeCommons
from damexCommons.tools.exchange_db import ExchangeDB
from damexCommons.tools.connections import get_commons


running_processes = []

def run_order_books_thread(exchange: str, base_asset: str, quote_asset: str, commons: ExchangeCommons) -> None:
    while True:
        try:
            running_processes.append(exchange + '__' + base_asset + '-' + quote_asset)
            tickers = OrderBooks(
                exchange=exchange, 
                base_asset=base_asset, 
                quote_asset=quote_asset, 
                commons=commons
            )
            tickers.run()
        except Exception as e:
            logging.info('---------------------failed %s %s %s', exchange, base_asset, quote_asset)
            logging.info('---------------------retry')
        time.sleep(5)
        
    
exchanges_included = [sys.argv[1]]
    
while True:    
    exchange_db = ExchangeDB(db_connection='data_collector')
    exchanges_info = exchange_db.fetch_exchanges_info_db(exchanges=exchanges_included)
    
    print('exchanges_info', exchanges_info)

    for exchange in exchanges_info:
        if exchange not in exchanges_included:
            continue
        for market in exchanges_info[exchange]:
            try:
                base_asset = market.split('-')[0]
                quote_asset = market.split('-')[1]
                if exchange + '__' + base_asset + '-' + quote_asset in running_processes:
                    logging.info('process already running %s %s %s', exchange, base_asset, quote_asset)
                    continue
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
                time.sleep(2)
    time.sleep(30)
