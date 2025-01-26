import asyncio
from damexCommons.base import TradeSide
from damexCommons.tools.dbs import get_exchange_db

exchange_db = get_exchange_db(db_connection='exchange')

#def test_fetch_active_alerts_db():
#    active_alerts = asyncio.run(exchange_db.fetch_active_alerts_db())
#    print('active_alerts', active_alerts)
#    assert True
    
#def test_fetch_open_orders_count_db():
#    open_orders_count = asyncio.run(exchange_db.fetch_open_orders_count_db(exchange='coinstore', base_asset='DAMEX', quote_asset='USDT', sides=[1, 2]))
#    print('open_orders_count', open_orders_count)
#    assert False

#def test_fetch_open_orders_db():
#    open_orders = asyncio.run(exchange_db.fetch_open_orders_db(
#        base_asset='DAMEX', 
#        quote_asset='USDT', 
#        size=100,
#        exchanges=['tidex'],
#        by_type=False
#    ))
#    print('open_orders', open_orders)
#    assert False
    
#def test_fetch_open_orders_by_bot_type_and_bot_id_db():
#    open_orders = asyncio.run(exchange_db.fetch_open_orders_by_bot_type_and_bot_id_db(base_asset='DAMEX', quote_asset='USDT', bot_type='maker', bot_id='1', size=100))
#    print('open_orders', open_orders)
#    assert False

#def test_fetch_open_orders_by_price_and_amount_db():
#    open_orders = asyncio.run(exchange_db.fetch_open_orders_by_price_and_amount_db(base_asset='DAMEX', quote_asset='USDT', price=0.0300, amount=1000))
#    print('open_orders', open_orders)
#    assert False


'''
def order_book_callback(order_book: dict) -> None:
    print('order_book', order_book)

def test_db_listen():
    exchange_db.db_listen(notifier='notify_order_book_damexusdt', callback=order_book_callback, test=True)
    assert True

def test_get_order_book_db():
    order_book = asyncio.run(exchange_db.get_order_book_db(base_asset='DAMEX', quote_asset='USDT', size=20, exchange='tidex'))
    assert len(order_book['asks']) > 0 or len(order_book['bids']) > 0
'''

'''
def test_fetch_exchanges_info_db_1():
    exchanges_info = exchange_db.fetch_exchanges_info_db()
    print('exchanges_info 1', exchanges_info)
    assert len(exchanges_info) > 0 

def test_fetch_exchanges_info_db_2():
    exchanges_info = exchange_db.fetch_exchanges_info_db(['tidex'])
    print('exchanges_info 2', exchanges_info)
    assert len(exchanges_info) > 0 
    
def test_fetch_trades_db_1():
    trades = asyncio.run(exchange_db.fetch_trades_db(exchanges=['coinstore', 'tidex'], base_asset='DAMEX', quote_asset='USDT', sides=[TradeSide.BUY.value, TradeSide.SELL.value], order_timestamp='ASC'))
    assert len(trades) > 0 
    
def test_fetch_trades_db_2():
    trades = asyncio.run(exchange_db.fetch_trades_db(exchanges=['coinstore', 'tidex'], base_asset='DAMEX', quote_asset='USDT', sides=[TradeSide.BUY.value, TradeSide.SELL.value], order_timestamp='ASC', bot_types=['vol', 'taker']))
    print('trades', trades)
    assert len(trades) > 0 
    
def test_get_main_price_parameters_db_1():
    main_price_parameters = asyncio.run(exchange_db.get_main_price_parameters_db(base_asset='DAMEX', quote_asset='USDT'))
    assert len(main_price_parameters) > 0 
    
def test_get_main_price_parameters_db_2():
    main_price_parameters = asyncio.run(exchange_db.get_main_price_parameters_db(base_asset='DAMEX', quote_asset='USDT', include_active_exchanges=True))
    assert len(main_price_parameters) > 0 and 'active_exchanges' in main_price_parameters

def test_get_trades_volume_db():
    bots_volume = asyncio.run(
        exchange_db.get_trades_volume_db(
            exchanges=['tidex', 'coinstore'],
            base_asset='DAMEX',
            quote_asset='USDT',
            sides=[1, 2],
            bot_types=['vol', 'taker']
        )
    )
    assert bots_volume > 0
'''

def test_get_asset_decimals():
    asset_decimals = asyncio.run(exchange_db.get_asset_decimals(asset='HOT'))
    print('asset_decimals', asset_decimals)
    assert False
