import time
import logging
from threading import Event
import asyncio
from damexCommons.base import OrderStatus
from damexCommons.businesses.base import SimpleBusiness

class CoinstoreSimpleBusiness(SimpleBusiness):
    
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