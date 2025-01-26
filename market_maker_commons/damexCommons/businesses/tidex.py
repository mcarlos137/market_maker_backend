import time
import logging
from threading import Event
import asyncio
from damexCommons.base import OrderStatus, Trade, TradeSide
from damexCommons.businesses.base import SimpleBusiness

class TidexSimpleBusiness(SimpleBusiness):

    def orders_check_thread(self, event: Event) -> None:    
        while True:
            if self.stop_check_threads['orders']:
                logging.info('STOPPING orders check thread==============')
                self.stop_check_threads['orders'] = False
                event.set()
                break   
            
            logging.info('========== START orders check thread ==========')
            orders_history = asyncio.run(self.execute(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, name='fetch_orders_history', attributes=()))             
            seconds_to_cancel: int = (12 * 60) if self.bot_type == 'maker' else 30
            for side in self.order_sides: 
                for active_order in self.active_orders[side].copy():
                    if active_order.creation_timestamp < (int(time.time() * 1e3) - (seconds_to_cancel * 1e3)):
                        try:
                            asyncio.run(self.cancel_order(order=active_order))
                        except Exception as e:
                             logging.error('cancel_order %s', e)
                        continue
                    try:
                        side = active_order.side
                        exchange_id = active_order.exchange_id
                        closed_order_founded = None
                        order_history = None
                        for order_history in orders_history:
                            if str(order_history['id']) == exchange_id:
                                closed_order_founded = order_history
                                break      
                        if closed_order_founded is None:
                            continue                   
                        logging.info('========== closed order founded ========== %s', closed_order_founded) 
                        if order_history is None:
                            return
                        if float(order_history['amount']) == float(order_history['dealStock']):
                            status = OrderStatus.FILLED
                        elif float(order_history['amount']) != float(order_history['dealStock']):
                            status = OrderStatus.PARTIALLY_FILLED
                        else:
                            status = OrderStatus.CANCELLED
                            
                        match status:
                            case OrderStatus.CANCELLED:
                                asyncio.run(self.cancel_order(order=active_order))
                            case OrderStatus.FILLED | OrderStatus.PARTIALLY_FILLED:
                                trade = Trade(bot_id=active_order.bot_id, strategy_id=active_order.strategy_id, base_asset=active_order.base_asset, quote_asset=active_order.quote_asset, timestamp=int(order_history['ftime'] * 1000), order_id=active_order.id, side=TradeSide.from_str(order_history['side'].upper()), price=float(order_history['price']), amount=float(order_history['amount']), fee={}, exchange_id=str(order_history['id']), exchange=active_order.exchange)
                                asyncio.run(self.bot_db.create_trade_db(trade=trade))
                                logging.info('trade created %s', trade)
                                asyncio.run(self.change_order_status(order=active_order, new_status=status))
                                if active_order in self.active_orders[active_order.side.name]: self.active_orders[active_order.side.name].remove(active_order)
                    except Exception as e:
                        logging.error('order_check thread %s %s %s', exchange_id, side, e)
                        
            logging.info('========== FINISH orders check thread ==========')             
            time.sleep(5)