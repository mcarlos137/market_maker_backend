from threading import Thread
import sys
import os
sys.path.append(os.getcwd())
from current_orders.base import CurrentOrders, CurrentOrdersPeriodDataType
from damexCommons.tools.exchange_db import ExchangeDB
from damexCommons.tools.dbs import get_exchange_db


def run_current_orders_thread(exchange: str, base_asset: str, quote_asset: str, exchange_db: ExchangeDB):
    current_orders = CurrentOrders(
        exchange=exchange, 
        base_asset=base_asset,
        quote_asset=quote_asset,
        exchange_db=exchange_db
    )
    current_orders.run()
    
def run_current_orders_period_data_type_thread(exchange: str, base_asset: str, quote_asset: str):
    current_orders_period_data_type = CurrentOrdersPeriodDataType(
        exchange=exchange, 
        base_asset=base_asset,
        quote_asset=quote_asset
    )
    current_orders_period_data_type.run()
    
exchange_db = get_exchange_db(db_connection='preprocessor')
exchanges_info = exchange_db.fetch_exchanges_info_db()

for exchange in exchanges_info:
    for market in exchanges_info[exchange]:
        base_asset: str = market.split('-')[0]
        quote_asset: str = market.split('-')[1]
        if exchanges_info[exchange][market]['preprocess']:     
            t_1 = Thread(target=run_current_orders_thread, args=(exchange, base_asset, quote_asset, exchange_db))
            t_1.start()
            t_2 = Thread(target=run_current_orders_period_data_type_thread, args=(exchange, base_asset, quote_asset))
            t_2.start()
