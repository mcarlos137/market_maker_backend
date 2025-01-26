import time
import logging
from threading import Event
import asyncio
from damexCommons.base import OrderStatus, Order, Trade, TradeSide, OrderSide
from damexCommons.businesses.base import SimpleBusiness

class AscendexSimpleBusiness(SimpleBusiness):
    
    def orders_check_thread(self, event: Event) -> None:
        while True:
            if self.stop_check_threads['orders']:
                logging.info('STOPPING orders check thread==============')
                self.stop_check_threads['orders'] = False
                event.set()
                break   
            logging.info('========== START orders check thread ==========')
            seconds_to_cancel: int = (12 * 60) if self.bot_type == 'maker' else 30
            for side in self.order_sides:       
                for active_order in self.active_orders[side].copy():
                    if active_order.creation_timestamp < (int(time.time() * 1e3) - (seconds_to_cancel * 1e3)):
                        try:
                            asyncio.run(self.cancel_order(order=active_order))
                        except Exception as e:
                             logging.error('cancel_order %s', e)
                        continue
                    order_id = None
                    try:
                        order_id = active_order.id
                        side = active_order.side
                        exchange_id = active_order.exchange_id
                        status = asyncio.run(self.execute(exchange=active_order.commons_exchange, base_asset=active_order.base_asset, quote_asset=active_order.quote_asset, name='fetch_order_status', attributes=(exchange_id,)))
                        match status:
                            case OrderStatus.CANCELLED:
                                asyncio.run(self.cancel_order(order=active_order))
                            case OrderStatus.FILLED | OrderStatus.PARTIALLY_FILLED:
                                asyncio.run(self.sync_order_trades(order=active_order, new_status=status))
                    except Exception as e:
                        logging.error('order_check thread %s %s %s', order_id, side, e)
                                
            logging.info('========== FINISH orders check thread ==========')                                           
            time.sleep(self.tick_time)
            
    async def sync_order_trades(self, order: Order, new_status: OrderStatus) -> None:
        try:
            order_filled_details = await self.execute(exchange=order.commons_exchange, base_asset=order.base_asset, quote_asset=order.quote_asset, name='fetch_ccxt_order_filled_short_details', attributes=(order.exchange_id,))
            logging.info('order_filled_details %s', order_filled_details)
            order_trades_db = await self.bot_db.fetch_order_trades_db(order_id=order.id)
            trade_amount = order_filled_details['filled']
            fee = order_filled_details['fee']
            if trade_amount == 0:
                return
            elif len(order_trades_db) > 0:
                total_trades_amount = 0
                for order_trade_db in order_trades_db:
                    total_trades_amount += order_trade_db.amount
                trade_amount = order_filled_details['filled'] - total_trades_amount
            trade = Trade(bot_id=order.bot_id, strategy_id=order.strategy_id, base_asset=order.base_asset, quote_asset=order.quote_asset, timestamp=int(time.time() * 1e3), order_id=order.id, side=TradeSide.SELL if order.side == OrderSide.ASK else TradeSide.BUY, price=order_filled_details['price'], amount=trade_amount, fee=fee, exchange_id='NONE', exchange=order.exchange)
            await self.bot_db.create_trade_db(trade=trade)
            logging.info('trade created %s', trade)
            await self.change_order_status(order=order, new_status=new_status)
            if new_status == OrderStatus.FILLED:
                if order in self.active_orders[order.side.name]: self.active_orders[order.side.name].remove(order)
        except Exception as e:
            logging.error(e)
    