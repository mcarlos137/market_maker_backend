import asyncio
import json
from pathlib import Path
import os
import ccxt
from damexCommons.base import OrderStatus, Order, OrderType, OrderSide
from damexCommons.tools.dbs import get_bot_db
from damexCommons.connectors.binance import BinanceCommons
from damexCommons.businesses.test import TestBusiness

#2024-07-16 01:36:23,898 INFO order status HOT/USDT 965982736 OrderStatus.FILLED
#2024-07-16 01:36:24,133 INFO order status HOT/USDT 965982875 OrderStatus.FILLED

'''
def test_sync_order_trades():
    with open(str(Path(os.getcwd()).parent.parent) + "/base/apis.json", encoding='UTF-8') as f:
        apis = json.load(f)
    api_or_wallet = 'binance__main'
    exchange = 'binance'
    base_asset = 'HOT'
    quote_asset = 'USDT'
    api_key = apis[api_or_wallet]['api_key']
    api_secret = apis[api_or_wallet]['api_secret']
    print('api_key', api_key)
    print('api_secret', api_secret)
    commons = {exchange + '__' + base_asset + '-' + quote_asset: BinanceCommons(exchange_connector=ccxt.binance({
        'apiKey': api_key,
        'secret': api_secret
    }), base_asset=base_asset, quote_asset=quote_asset)}
    simple_business = TestBusiness(
        bot_id='101',
        bot_type='taker',
        active=False,
        bot_db=get_bot_db(db_connection='bot', bot_type='taker'),
        commons=commons,
        exchange=exchange,
        base_asset=base_asset,
        quote_asset=quote_asset,
        tick_time=3
    )
    order = Order(
        id= '6995DDD75F7C4B3B',
        bot_id= '101',
        strategy_id='taker_binance_holo_v1',
        base_asset='HOT',
        quote_asset='USDT',
        creation_timestamp=1721093765136,
        type=OrderType.LIMIT,
        price=0.001925,
        amount=10000,
        last_status=OrderStatus.CREATED,
        last_update_timestamp=1721093789960,
        side=OrderSide.ASK,
        aux=False,
        exchange_id='965982875',
        exchange='binance',
    )
    asyncio.run(simple_business.sync_order_trades(order=order, new_status=OrderStatus.FILLED))
    assert True
'''