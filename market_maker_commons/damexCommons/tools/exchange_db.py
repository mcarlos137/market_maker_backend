import json
import select
import asyncio
import time
import psycopg2
import psycopg2.pool
from typing import Optional, Callable
from contextlib import contextmanager
from damexCommons.base import EXCHANGE_USE, FEE_ASSET_TYPE, STATUS, TradeSide, Trade, Order, OrderType, OrderSide, OrderStatus
from damexCommons.tools.utils import get_config

TYPES: dict = {
    'price_change_percent': 1,
    'balance_out_of_limits': 2,
    'maker_orders_out_of_range': 3,
    'ask_ceiling_or_bid_floor_discover': 4
}

class ExchangeDB:
    
    def __init__(self, db_connection: str):
        db_parameters = json.loads(open(get_config()['db_file_location'], 'r', encoding='UTF-8').read())        
        self.dbpool = psycopg2.pool.ThreadedConnectionPool(
                host=db_parameters[db_connection]['host'],
                port=db_parameters[db_connection]['port'],
                dbname=db_parameters[db_connection]['dbname'],
                user=db_parameters[db_connection]['user'],
                password=db_parameters[db_connection]['password'],
                minconn=db_parameters[db_connection]['minconn'],
                maxconn=db_parameters[db_connection]['maxconn']
                )
        
    @contextmanager
    def db_cursor(self):
        conn = self.dbpool.getconn()
        try:
            with conn.cursor() as cur:
                yield cur
                conn.commit()
        except:
            conn.rollback()
            raise
        finally:
            self.dbpool.putconn(conn)
         
    def db_listen(self, notifier: str, callback: Callable, test: Optional[bool] = False):
        conn = self.dbpool.getconn()
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        cursor.execute('LISTEN %s;' % (notifier))
        while True:
            select.select([conn],[],[])   #sleep until there is some data
            conn.poll()                   #get the message
            while conn.notifies:
                notification =  conn.notifies.pop()  #pop notification from list
                #now do anything needed! 
                channel = notification.channel
                match channel:
                    case 'notify_order_book_damexusdt':
                        order_book = asyncio.run(self.get_order_book_db(base_asset='DAMEX', quote_asset='USDT', size=100))
                        callback(order_book)
                        if test:
                            break
            if test:
                break
                             
    def fetch_exchanges_info_db(self, exchanges: Optional[list[str]] = None) -> dict:
        try:
            with self.db_cursor() as cursor:
                exchanges_info: dict = {}
                query = 'SELECT * FROM public.fetch_exchanges_info()'
                if exchanges is not None and len(exchanges) > 0:
                    query = 'SELECT * FROM public.fetch_exchanges_info(ARRAY[%s])' % (exchanges)
                cursor.execute(query)
                records = cursor.fetchall()
                for r in records:
                    if r[0] not in exchanges_info:
                        exchanges_info[r[0]] = {}
                    exchanges_info[r[0]][r[1]] = {
                        'price_decimals': int(r[2]),
                        'base_amount_decimals': int(r[3]),
                        'quote_amount_decimals': int(r[4]),
                        'base_min_amount': float(r[5]),
                        'quote_min_amount': float(r[6]),
                        'market_use': EXCHANGE_USE[int(r[7])],
                        'status_exchange': STATUS[int(r[8])],
                        'status_market': STATUS[int(r[9])],
                        'status_exchange_market': STATUS[int(r[10])],
                        'buy_fee_percentage': float(r[11]),
                        'buy_fee_asset_type': FEE_ASSET_TYPE[int(r[12])],
                        'sell_fee_percentage': float(r[13]),
                        'sell_fee_asset_type': FEE_ASSET_TYPE[int(r[14])],
                        'market_main_price_exist': bool(r[15]),
                        'data_collect': bool(r[16]),
                        'preprocess': bool(r[17]),
                    }
                return exchanges_info
        except psycopg2.Error as e:
            raise e   
        
    async def fetch_trades_db(self, exchanges: list[str], base_asset: str, quote_asset: str, sides: list[int], order_timestamp: str, initial_timestamp: Optional[int] = None, final_timestamp: Optional[int] = None, offset: int = 0, bot_types: Optional[str] = None) -> list[Trade]:
        try:
            with self.db_cursor() as cursor:
                trades: list[Trade] = []
                #FUNCTION
                if bot_types is None or len(bot_types) == 0:
                    query = 'SELECT * FROM public.fetch_trades(ARRAY[%s], %r, %r, ARRAY[%s], %s, %s, %r, %s)' % (
                        exchanges, 
                        base_asset, 
                        quote_asset, 
                        sides, 
                        'null' if initial_timestamp is None else initial_timestamp, 
                        'null' if final_timestamp is None else final_timestamp,
                        order_timestamp, 
                        offset
                    )
                else:
                    query = 'SELECT * FROM public.fetch_trades(ARRAY[%s], %r, %r, ARRAY[%s], %s, %s, %r, %s, ARRAY[%s]);' % (
                        exchanges, 
                        base_asset, 
                        quote_asset, 
                        sides, 
                        'null' if initial_timestamp is None else initial_timestamp, 
                        'null' if final_timestamp is None else final_timestamp,
                        order_timestamp, 
                        offset,
                        bot_types
                    )
                cursor.execute(query)
                records = cursor.fetchall()
                for r in records:   
                    trades.append(Trade(bot_id=r[0], strategy_id=r[1], base_asset=r[2], quote_asset=r[3], timestamp=r[4], order_id=r[5], side=TradeSide(r[6]).name, price=float(r[7] / 1e6), amount=float(r[8] / 1e6), fee=r[9], exchange_id=r[10], exchange=r[11]))
                return trades
        except psycopg2.Error as e:
            raise e
        
    async def fetch_trades_by_bot_db(self, bot_type: str, bot_id: str, order_timestamp: str, initial_timestamp: Optional[int] = None, final_timestamp: Optional[int] = None, offset: int = 0) -> list[Trade]:
        try:
            with self.db_cursor() as cursor:
                trades: list[Trade] = []
                #FUNCTION
                query = 'SELECT * FROM public.fetch_trades(%r, %r, %s, %s, %r, %s)' % (
                    bot_type,
                    bot_id,
                    'null' if initial_timestamp is None else initial_timestamp, 
                    'null' if final_timestamp is None else final_timestamp,
                    order_timestamp, 
                    offset
                )
                cursor.execute(query)
                records = cursor.fetchall()
                for r in records:   
                    trades.append(Trade(bot_id=r[0], strategy_id=r[1], base_asset=r[2], quote_asset=r[3], timestamp=r[4], order_id=r[5], side=TradeSide(r[6]).name, price=float(r[7] / 1e6), amount=float(r[8] / 1e6), fee=r[9], exchange_id=r[10], exchange=r[11]))
                return trades
        except psycopg2.Error as e:
            raise e


    async def get_main_price_parameters_db(self, base_asset: str, quote_asset: str, include_active_exchanges: Optional[bool] = False) -> dict:
        with self.db_cursor() as cursor:
            query_1 = 'SELECT * FROM public.get_main_price_parameters(%r, %r);' % (base_asset, quote_asset)
            cursor.execute(query_1)
            records_1 = cursor.fetchone()
            if records_1 is None:
                return None
            main_price_parameters: dict = {'main_price_type': records_1[1], 'weighted_price_limit_time': records_1[2], 'weighted_price_max_tickers_per_source': records_1[3], 'weighted_price_exponential_factor': records_1[4], 'price_floor': records_1[5], 'price_ceiling': records_1[6]}
            if include_active_exchanges:    
                active_exchanges = []
                query_2 = 'SELECT "EXCHANGES_NEW".name FROM "MAIN_PRICES_active_exchanges_new" JOIN "EXCHANGES_NEW" ON "EXCHANGES_NEW".id = "MAIN_PRICES_active_exchanges_new".exchangenew_id WHERE "MAIN_PRICES_active_exchanges_new".mainprice_id = %s;' % (records_1[0])
                cursor.execute(query_2)
                records_2 = cursor.fetchall()
                for r in records_2:
                    active_exchanges.append(r[0].lower())
                main_price_parameters['active_exchanges'] = active_exchanges
            return main_price_parameters

    async def get_trades_volume_db(self, exchanges: list[str], base_asset: str, quote_asset: str, sides: list[int], bot_types: list[str], initial_timestamp: int = 0, final_timestamp: int = 99999999999999999, turnover: bool = False) -> float:
        with self.db_cursor() as cursor:
            #FUNCTION
            query = 'SELECT public.get_trades_volume(ARRAY[%s], %r, %r, ARRAY[%s], %s, %s, %s, ARRAY[%s])' % (
                exchanges, 
                base_asset, 
                quote_asset, 
                sides, 
                initial_timestamp,
                final_timestamp,
                turnover, 
                bot_types
            )
            cursor.execute(query)
            record = cursor.fetchone()
            return record[0]
        
    async def get_order_book_db(self, base_asset: str, quote_asset: str, size: int, exchange: Optional[str] = None):
        try:
            with self.db_cursor() as cursor:
                #FUNCTION
                if exchange is not None:
                    query = 'SELECT * FROM public.get_order_book(%r, %r, %s, %r)' % (base_asset, quote_asset, size, exchange)
                else:
                    query = 'SELECT * FROM public.get_order_book(%r, %r, %s)' % (base_asset, quote_asset, size)
                cursor.execute(query)
                records = cursor.fetchall()  
                order_book = {'asks': [], 'bids': []}
                asks = {}
                bids = {} 
                for r in records:
                    amount = float(r[2])
                    price = float(r[1])
                    order_side = r[3]
                    if order_side == 'ASK':
                        if price in asks:
                            asks[price] += amount 
                        else:
                            asks[price] = amount
                    else:    
                        if price in bids:
                            bids[price] += amount 
                        else:
                            bids[price] = amount
                
                asks = sort(asks, reverse=False)
                bids = sort(bids, reverse=True)
                
                accumulated_ask = 0
                for ask in asks:
                    accumulated_ask += asks[ask]
                    order_book['asks'].append([ask, asks[ask], accumulated_ask])
                accumulated_bid = 0
                for bid in bids:
                    accumulated_bid += bids[bid]
                    order_book['bids'].append([bid, bids[bid], accumulated_bid])
                            
                return order_book
        except psycopg2.Error as e:
            raise e
    
    async def get_trades_sum_db(self, exchange: str, base_asset: str, quote_asset: str, bot_type: str, trade_side: TradeSide, timestamp: int) -> float:
        try:
            with self.db_cursor() as cursor:
                query = 'SELECT SUM(amount) FROM trades_damexusdt WHERE exchange = %r AND base_asset = %r AND quote_asset = %r AND strategy LIKE %s AND side = %s AND timestamp >= %s;' % (
                    exchange,
                    base_asset,
                    quote_asset,
                    '\'%' + bot_type + '%\'',
                    trade_side.value,
                    timestamp
                )
                cursor.execute(query)
                record = cursor.fetchone()
                if record[0] is None:
                    return 0
                return float(record[0]) / 1e6
        except psycopg2.Error as e:
            raise e
        
    async def fetch_open_orders_db(
        self, 
        base_asset: str, 
        quote_asset: str, 
        size: Optional[int] = 100, 
        exchanges: Optional[list[str]] = None, 
        bot_types: Optional[list[str]] = None, 
        bot_id: Optional[str] = None, 
        price: Optional[float] = None,
        amount: Optional[float] = None,
        by_type: Optional[bool] = True
    ) -> dict[str, list[Order]] | list[Order]:
        try:
            with self.db_cursor() as cursor:
                orders_by_type: dict[str, list[Order]] = {'ASK': [], 'BID': []}
                orders: list[Order] = []
                #FUNCTION
                query = 'SELECT * FROM public.fetch_open_orders(%r, %r, %s, ARRAY[%s], ARRAY[%s], %r, %s, %s)' % (base_asset, quote_asset, size, exchanges, bot_types, bot_id, price, amount)
                query = query.replace('ARRAY[None]', 'null')
                query = query.replace('None', 'null')
                cursor.execute(query)
                records = cursor.fetchall()
                for r in records:
                    order = Order(id=r[0], bot_id=r[1], strategy_id=r[2], base_asset=r[3], quote_asset=r[4], creation_timestamp=r[5], type=OrderType(r[6]), price=float(r[7] / 1e6), amount=float(r[8] / 1e6), last_status=OrderStatus(r[9]), last_update_timestamp=r[10], exchange_id=r[11], side=OrderSide(r[12]), exchange=r[13], aux=r[14])
                    orders_by_type[order.side.name].append(order) if by_type else orders.append(order)
                return orders_by_type if by_type else orders
        except psycopg2.Error as e:
            raise e   
    
    async def fetch_orders_last_12_minutes_db(
        self, 
        base_asset: str, 
        quote_asset: str, 
        size: Optional[int] = 100, 
        exchanges: Optional[list[str]] = None, 
        bot_types: Optional[list[str]] = None, 
        bot_id: Optional[str] = None, 
        price: Optional[float] = None,
        amount: Optional[float] = None,
        by_type: Optional[bool] = True
    ) -> dict[str, list[Order]] | list[Order]:
        try:
            with self.db_cursor() as cursor:
                orders_by_type: dict[str, list[Order]] = {'ASK': [], 'BID': []}
                orders: list[Order] = []
                #FUNCTION
                query = 'SELECT * FROM public.fetch_orders_last_12_minutes(%r, %r, %s, ARRAY[%s], ARRAY[%s], %r, %s, %s)' % (base_asset, quote_asset, size, exchanges, bot_types, bot_id, price, amount)
                query = query.replace('ARRAY[None]', 'null')
                query = query.replace('None', 'null')
                cursor.execute(query)
                records = cursor.fetchall()
                for r in records:
                    order = Order(id=r[0], bot_id=r[1], strategy_id=r[2], base_asset=r[3], quote_asset=r[4], creation_timestamp=r[5], type=OrderType(r[6]), price=float(r[7] / 1e6), amount=float(r[8] / 1e6), last_status=OrderStatus(r[9]), last_update_timestamp=r[10], exchange_id=r[11], side=OrderSide(r[12]), exchange=r[13], aux=r[14])
                    orders_by_type[order.side.name].append(order) if by_type else orders.append(order)
                return orders_by_type if by_type else orders
        except psycopg2.Error as e:
            raise e   
    
            
    async def cancel_old_orders_db(self):
        try:
            base_timestamp = int(time.time() * 1000) - (12 * 60 * 1000)
            with self.db_cursor() as cursor:
                #STORED PROCEDURE
                query = 'CALL public.cancel_old_orders(%r)' % (base_timestamp)
                cursor.execute(query)
        except psycopg2.Error as e:
            raise e

    async def fetch_active_alerts_db(self):
        try:
            alerts: list = []
            with self.db_cursor() as cursor:
                #FUNCTION
                query = 'SELECT * FROM public.fetch_active_alerts();'
                cursor.execute(query)
                records = cursor.fetchall()
                for r_1 in records:
                    alert_id = r_1[0]
                    name = str(r_1[1])
                    alert_type = list(TYPES.keys())[list(TYPES.values()).index(r_1[2])]
                    config = json.loads(r_1[3])
                    message_output = str(r_1[4])
                    telegram_group_id = str(r_1[5])
                    telegram_auth_token = str(r_1[6])
                    alert: dict = {
                        'id': alert_id,
                        'name': name,
                        'type': alert_type,
                        'config': config,
                        'message_output': message_output,
                        'telegram_group_id': telegram_group_id,
                        'telegram_auth_token': telegram_auth_token,
                        'exchanges': []
                    }
                    query_2: str = 'SELECT public."EXCHANGES_NEW".name FROM public."ALERTS_active_exchanges_new" JOIN public."EXCHANGES_NEW" ON public."ALERTS_active_exchanges_new".exchangenew_id = public."EXCHANGES_NEW".id WHERE public."ALERTS_active_exchanges_new".alert_id = %s;' % (alert_id)
                    cursor.execute(query_2)
                    records_2: list = cursor.fetchall()
                    for r_2 in records_2:
                        alert['exchanges'].append(str(r_2[0]).lower())
                    alerts.append(alert)
            return alerts
        except psycopg2.Error as e:
            raise e
        
    async def fetch_open_orders_count_db(self, exchange: str, base_asset: str, quote_asset: str, sides: list[int]):
        orders_count_by_side: dict = {OrderSide.ASK.name: 0, OrderSide.BID.name: 0}
        with self.db_cursor() as cursor:
            query = 'SELECT * FROM public.fetch_open_orders_count(%r, %r, ARRAY[%s], %r)' % (base_asset, quote_asset, sides, exchange)
            cursor.execute(query)
            records = cursor.fetchall()
            for r in records:
                order_side = OrderSide.from_id(r[0]).name
                order_side_count = int(r[1])
                orders_count_by_side[order_side] = order_side_count
            return orders_count_by_side
        
    async def get_asset_decimals(self, asset: str):
        with self.db_cursor() as cursor:
            query = 'SELECT amount_decimals FROM public."ASSETS" WHERE name = %r;' % (asset)
            cursor.execute(query)
            records = cursor.fetchone()
            return int(records[0])

    
def sort(object: dict={}, reverse: bool=False): 
    sorted_object = {}
    for i in sorted(object.keys(), key=float, reverse=reverse):
        sorted_object[i] = object[i]
    return sorted_object
