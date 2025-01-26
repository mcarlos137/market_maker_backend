from threading import Thread
import sys
import os
import logging
sys.path.append(os.getcwd())
from trades.base import Trades
from damexCommons.businesses.base import ExchangeCommons
from damexCommons.tools.exchange_db import ExchangeDB
from damexCommons.tools.connections import get_commons


def run_trades_thread(exchange: str, base_asset: str, quote_asset: str, commons: ExchangeCommons):
    trades = Trades(
        exchange=exchange, 
        base_asset=base_asset, 
        quote_asset=quote_asset, 
        commons=commons
    )
    trades.run()
    
exchanges_markets_included = [
    'binance_HOT-USDT', 
    'bitmart_HOT-USDT', 
    'tidex_DAMEX-USDT', 
    'ascendex_DAMEX-USDT', 
    'mexc_DAMEX-USDT', 
    'coinstore_DAMEX-USDT', 
    'bitmart_DAMEX-USDT'
]

exchange_db = ExchangeDB(db_connection='data_collector')
exchanges_info = exchange_db.fetch_exchanges_info_db()

for exchange in exchanges_info:
    for market in exchanges_info[exchange]:
        if (exchange + '_' + market) not in exchanges_markets_included:
            continue
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
            t = Thread(target=run_trades_thread, args=(exchange, base_asset, quote_asset, commons,))
            t.start()    
