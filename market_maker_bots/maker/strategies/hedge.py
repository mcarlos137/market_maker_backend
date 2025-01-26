import time
import logging
import random
from typing import Dict, List
import os
import sys
sys.path.append(os.getcwd())
from maker.base import MakerBotBase, MakerBot
from damexCommons.base import OrderStatus, Trade, TradeSide, Order, OrderSide, OrderType
from damexCommons.tools.damex_http_client import get_main_price


class MakerBotHedge(MakerBot):
    
    def __init__(self, maker_bot_base: MakerBotBase) -> None:
        super().__init__(maker_bot_base=maker_bot_base)
        
    async def sync_order_trades(self, order: Order, new_status: OrderStatus) -> None:
        try:
            order_trades = await self.execute(exchange=order.commons_exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, name='fetch_order_trades', attributes=(order.exchange_id,))
            order_trades_db = await self.bot_db.fetch_order_trades_db(order_id=order.id)
            for order_trade in order_trades:
                founded = False
                for order_trade_db in order_trades_db:
                    if order_trade['id'] == order_trade_db.exchange_id:
                        founded = True
                        break
                if not founded:
                    trade = Trade(bot_id=self.bot_id, strategy_id=self.strategy['id'], base_asset=self.base_asset, quote_asset=self.quote_asset, timestamp=order_trade['timestamp'], order_id=order.id, side=TradeSide.from_str(order_trade['side'].upper()), price=float(order_trade['price']), amount=float(order_trade['amount']), fee=order_trade['fee'], exchange_id=order_trade['id'], exchange=self.exchange)
                    await self.bot_db.create_trade_db(trade=trade)
                    logging.info('trade created %s', trade)
                    await self.hedge_order(order=order)
            await self.change_order_status(order=order, new_status=new_status)
            if new_status == OrderStatus.FILLED:
                if order in self.active_orders[order.side.name]: self.active_orders[order.side.name].remove(order)
        except Exception as e:
            logging.error(e)
    
        
    async def refresh_orders(self, sides: list[str]) -> None:
        try:
            self.main_price = await get_main_price(base_asset=self.base_asset, quote_asset=self.quote_asset, price_decimals=self.commons[self.exchange + '__' + self.pair].price_decimals)
            for side in sides:
                logging.info('cancelling %s orders %s', side, len(self.active_orders[side]))
                await self.cancel_all_orders(side=side)
            balance = await self.execute(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, name='fetch_balance', attributes=())
            available_base_amount = float(balance[self.base_asset]['available'])
            available_quote_amount = float(balance[self.quote_asset]['available'])
            total_base_amount = float(balance[self.base_asset]['total'])
            total_quote_amount = float(balance[self.quote_asset]['total'])
            order_book = await self.execute(exchange=self.exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, name='fetch_order_book', attributes=())
            orders_to_create: Dict[str, List[Order]] = {OrderSide.ASK.name: [], OrderSide.BID.name: []}
            for side in sides:
                self.order_spread = 0
                self.order_amount = 0
                self.order_total_amount = 0
                self.order_refresh_timestamp[side] = int(time.time() * 1e3)
                i = 0
                self.order_spread = self.strategy['spread'][side]
                self.order_amount = round(self.strategy['order_amount'][side] + random.uniform(0, 10), self.commons[self.exchange + '__' + self.pair].base_amount_decimals)  
                while i < self.strategy['order_levels'][side]:
                    i += 1    
                    price = (self.main_price - (self.main_price * self.order_spread / 100)) if side == OrderSide.BID.name else (self.main_price + (self.main_price * self.order_spread / 100))
                    price = round(price, self.commons[self.exchange + '__' + self.pair].price_decimals)
                    timestamp = int(time.time() * 1e3)
                    order_id = ''.join(random.choice('0123456789ABCDEF') for i in range(16))
                    order_to_create = Order(
                        id=order_id, 
                        bot_id=self.bot_id, 
                        strategy_id=self.strategy['id'], 
                        base_asset=self.base_asset, 
                        quote_asset=self.quote_asset,
                        creation_timestamp=timestamp,
                        type=OrderType.LIMIT,
                        price=float(price),
                        amount=float(self.order_amount),
                        last_status=OrderStatus.PENDING_TO_CREATE,
                        last_update_timestamp=int(time.time() * 1e3),
                        side=OrderSide.from_str(side),
                        exchange=self.exchange
                    )       
                    orders_to_create[side].append(order_to_create)
                    match side:
                        case OrderSide.BID.name:
                            if len(order_book['asks']) > 0 and float(order_book['asks'][0][0]) <= price:
                                excluded_order = orders_to_create[side].pop()
                                logging.info('excluding order %s by order book level', excluded_order)
                                self.increment_side_levels_value(side=side, add_to_order_total_amount=False)
                                continue
                        case OrderSide.ASK.name:
                            if len(order_book['bids']) > 0 and float(order_book['bids'][0][0]) >= price:
                                excluded_order = orders_to_create[side].pop()
                                logging.info('excluding order %s by order book level', excluded_order)
                                self.increment_side_levels_value(side=side, add_to_order_total_amount=False)
                                continue
                    if available_base_amount <= 0 and side == OrderSide.ASK.name:
                        excluded_order = orders_to_create[side].pop()
                        logging.info('excluding order %s by low balance', excluded_order)
                        break
                    if available_quote_amount <= 0 and side == OrderSide.BID.name:
                        excluded_order = orders_to_create[side].pop()
                        logging.info('excluding order %s by low balance', excluded_order)
                        break
                    if side == OrderSide.ASK.name:
                        if self.target is not None and self.target['asset'] == self.base_asset and self.target['operation'] == TradeSide.SELL.name:
                            base_asset_diff = self.target['initial_asset_amount'] - total_base_amount
                            if base_asset_diff + (self.order_total_amount + self.order_amount) > self.target['operation_amount']:
                                excluded_order = orders_to_create[OrderSide.ASK.name].pop()
                                logging.info('excluding order %s because target reached', excluded_order)
                                break
                        if self.order_amount + self.commons[self.exchange + '__' + self.pair].base_min_amount > available_base_amount:
                            excluded_order = orders_to_create[OrderSide.ASK.name].pop()
                            logging.info('excluding order %s because balance lower than min amount', excluded_order)
                            break
                        base_asset_diff = self.balance_1h_start[self.base_asset] - total_base_amount
                        if base_asset_diff + (self.order_total_amount + self.order_amount) > self.strategy['trade_amount_limit_1h'][TradeSide.SELL.name]:
                            excluded_order = orders_to_create[OrderSide.ASK.name].pop()
                            logging.info('excluding order %s by 1h trade limit', excluded_order)
                            break
                    if side == OrderSide.BID.name:
                        if self.target is not None and self.target['asset'] == self.base_asset and self.target['operation'] == TradeSide.BUY.name:
                            base_asset_diff = total_base_amount - self.target['initial_asset_amount']
                            if base_asset_diff + (self.order_total_amount + self.order_amount) > self.target['operation_amount']:
                                excluded_order = orders_to_create[OrderSide.BID.name].pop()
                                logging.info('excluding order %s because target reached', excluded_order)
                                break
                        if ((self.order_total_amount + self.order_amount) * price) + self.commons[self.exchange + '__' + self.pair].quote_min_amount > available_quote_amount:
                            excluded_order = orders_to_create[OrderSide.BID.name].pop()
                            logging.info('excluding order %s because balance lower than min amount', excluded_order)
                            continue
                        quote_asset_diff = self.balance_1h_start[self.quote_asset] - total_quote_amount
                        if quote_asset_diff + ((self.order_total_amount + self.order_amount) * self.main_price) > (self.strategy['trade_amount_limit_1h'][TradeSide.BUY.name] * self.main_price):
                            excluded_order = orders_to_create[OrderSide.BID.name].pop()
                            logging.info('excluding order %s by 1h trade limit', excluded_order)
                            break     
                    
                    # Adding next level values
                    self.increment_side_levels_value(side=side, add_to_order_total_amount=True)
                                               
            for side in sides:
                logging.info('creating %s %s orders', len(orders_to_create[side]), side)
                for order_to_create in orders_to_create[side]:
                    await self.create_order(order=order_to_create)
        except Exception as e:
            logging.error('refresh orders %s', e)
                        
    async def hedge_order(self, order: Order) -> None:
        balance_aux = await self.execute(exchange='b2c2', base_asset=self.base_asset, quote_asset=self.quote_asset, name='fetch_balance', attributes=())
        logging.info('---------------balance_aux %s', balance_aux)
        logging.info('---------------order %s', order)