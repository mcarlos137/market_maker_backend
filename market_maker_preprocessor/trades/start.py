from threading import Thread
import sys
import os
sys.path.append(os.getcwd())
from trades.base import TradesPeriodDataType
from damexCommons.tools.dbs import get_exchange_db

    
def run_trades_period_data_type_thread(exchange: str, base_asset: str, quote_asset: str):
    trades_period_data_type = TradesPeriodDataType(
        exchange=exchange, 
        base_asset=base_asset,
        quote_asset=quote_asset
    )
    trades_period_data_type.run()
    
exchange_db = get_exchange_db(db_connection='preprocessor')
exchanges_info = exchange_db.fetch_exchanges_info_db()

for exchange in exchanges_info:
    for market in exchanges_info[exchange]:
        base_asset: str = market.split('-')[0]
        quote_asset: str = market.split('-')[1]
        if exchanges_info[exchange][market]['preprocess']:
            t = Thread(target=run_trades_period_data_type_thread, args=(exchange, base_asset, quote_asset))
            t.start()    
