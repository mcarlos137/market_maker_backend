from threading import Thread
import time
import logging
import sys
import os
import asyncio
from typing import Optional
sys.path.append(os.getcwd())
from current_orders_cancel_old.base import CurrentOrdersCancelOld
from damexCommons.businesses.base import ExchangeCommons
from damexCommons.tools.dbs import get_exchange_db
from damexCommons.tools.connections import get_commons

exchanges_with_aux = ['ascendex'] 
allowed_markets = ['DAMEX-USDT', 'HOT-USDT']

def run_current_orders_cancel_old_thread(exchange: str, base_asset: str, quote_asset: str, commons: ExchangeCommons, commons_aux: Optional[ExchangeCommons]):
    current_orders_cancel_old = CurrentOrdersCancelOld(
        exchange=exchange, 
        base_asset=base_asset, 
        quote_asset=quote_asset, 
        commons=commons,
        commons_aux=commons_aux
    )
    current_orders_cancel_old.run()
    
exchange_db = get_exchange_db(db_connection='support_scripts')
exchanges_info = exchange_db.fetch_exchanges_info_db()

for exchange in exchanges_info:
    for market in exchanges_info[exchange]:
        if market not in allowed_markets:
            continue
        try:
            base_asset = market.split('-')[0]
            quote_asset = market.split('-')[1]
            commons_aux = None
            commons = get_commons(
                base_asset=base_asset,
                quote_asset=quote_asset,
                exchange_or_connector=exchange,
                api_or_wallet=exchange + '__' + 'main'
            )
            if exchange in exchanges_with_aux:
                commons_aux = get_commons(
                    base_asset=base_asset,
                    quote_asset=quote_asset,
                    exchange_or_connector=exchange,
                    api_or_wallet=exchange + '__' + 'main_aux'
                )
        except Exception as e:
            logging.error('exception %s', e)
            continue
        t = Thread(target=run_current_orders_cancel_old_thread, args=(exchange, base_asset, quote_asset, commons, commons_aux,))
        t.start()    
        
while True:
    time.sleep(10)
    asyncio.run(exchange_db.cancel_old_orders_db())
