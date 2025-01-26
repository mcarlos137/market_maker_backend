import psycopg2
import psycopg2.pool
from contextlib import contextmanager
import time
import json
from damexCommons.base import Order, OrderStatus, OrderSide, Trade, TradeSide
from damexCommons.tools.utils import get_config

class BotDB:
    
    def __init__(self,
                db_connection: str,
                bot_type: str = None 
                ):
        self.schema = bot_type + '_bots'
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
                        
    async def create_order_db(self, order: Order):
        try:
            with self.db_cursor() as cursor:
                #STORED PROCEDURE
                query = 'CALL public.create_order(%r, %r, %r, %r, %r, %r, %s, %s, %s, %s, %s, %s, %r, %s, %r, %s)' % (
                    self.schema, 
                    order.id, 
                    order.bot_id, 
                    order.strategy_id, 
                    order.base_asset, 
                    order.quote_asset, 
                    order.creation_timestamp, 
                    order.type.value, 
                    order.amount * 1e6,  
                    order.price * 1e6, 
                    order.last_status.value, 
                    order.last_update_timestamp, 
                    order.exchange_id, 
                    order.side.value, 
                    order.exchange, 
                    order.aux
                )
                cursor.execute(query)
        except psycopg2.Error as e:
            raise e
      
    async def change_order_status_db(self, order_id: str, status: OrderStatus) -> None:
        try:
            with self.db_cursor() as cursor:
                #STORED PROCEDURE
                query = 'CALL public.change_order_status(%r, %r, %s, %s)' % (self.schema, order_id, int(time.time() * 1e3), status.value)
                cursor.execute(query)
        except psycopg2.Error as e:
            raise e    
        
    async def fetch_order_trades_db(self, order_id: str) -> list[Trade]:
        try:
            with self.db_cursor() as cursor:
                trades: list[Trade] = []
                #FUNCTION
                query = 'SELECT * FROM public.fetch_order_trades(%r, %r)' % (self.schema, order_id)
                cursor.execute(query)
                records = cursor.fetchall()
                for r in records:   
                    trades.append(Trade(bot_id=r[0], strategy_id=r[1], base_asset=r[2], quote_asset=r[3], timestamp=r[4], order_id=r[5], side=TradeSide(r[6]), price=float(r[7] / 1e6), amount=float(r[8] / 1e6), fee=r[9], exchange_id=r[10], exchange=r[11]))
                return trades
        except psycopg2.Error as e:
            raise e   
        
    async def create_trade_db(self, trade: Trade):
        try:
            with self.db_cursor() as cursor:
                #FUNCTION
                query = 'CALL public.create_trade(%r, %r, %r, %r, %r, %s, %r, %s, %s, %s, %r, %r, %r)' % (
                    self.schema, 
                    trade.bot_id, 
                    trade.strategy_id, 
                    trade.base_asset, 
                    trade.quote_asset, 
                    trade.timestamp, 
                    trade.order_id, 
                    trade.side.value, 
                    trade.price * 1e6, 
                    trade.amount * 1e6, 
                    json.dumps(trade.fee), 
                    trade.exchange_id, 
                    trade.exchange
                )
                cursor.execute(query)
        except psycopg2.Error as e:
            raise e
        
    async def order_by_strategy_side_price_exist_db(self, order_side: OrderSide, price: float, exchange: str):
        query = 'SELECT count(id) FROM %s."ORDERS" WHERE exchange = %s AND price = %s AND side = %s AND last_status = %s;' % (
            self.schema,
            '\'%' + exchange.capitalize() + '%\'', 
            int(price * 1000000), 
            order_side.value, 
            1
            )
        with self.db_cursor() as cursor:
            cursor.execute(query)
            record = cursor.fetchone()
            return record[0] > 0
                        