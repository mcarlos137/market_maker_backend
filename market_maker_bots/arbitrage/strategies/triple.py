import os
import sys
import logging
import time
import json
import asyncio
from threading import Thread, Event
from damexCommons.base import Trade, TradeSide
sys.path.append(os.getcwd())
from arbitrage.base import ArbitrageBotBase, ArgitrageBot
from damexCommons.tools.damex_http_client import execute_emulated_balance_new, fetch_emulated_balance_new


class ArbitrageBotTriple(ArgitrageBot):
    
    def __init__(self, arbitrage_bot_base: ArbitrageBotBase) -> None:
        super().__init__(arbitrage_bot_base=arbitrage_bot_base)
        
    async def start(self) -> None:
        await self.refresh_strategy_and_target()
        if not self.testing:
            t_1 = Thread(target=self.orders_check_thread, args=(Event(),))
            t_1.start()       
        for exchange in self.exchanges:
            for base_asset in self.base_assets:
                thread_id_1 = exchange + '__' + base_asset + '-' + self.strategy['pivot_asset']
                self.stop_check_threads[thread_id_1] = False
                thread_1 = Thread(target=self.order_book_thread, args=(exchange, base_asset, self.strategy['pivot_asset'], Event(),))
                thread_1.start()
                
                thread_id_2 = exchange + '__' + self.strategy['pivot_asset'] + '-' + self.quote_asset
                self.stop_check_threads[thread_id_2] = False
                thread_2 = Thread(target=self.order_book_thread, args=(exchange, self.strategy['pivot_asset'], self.quote_asset, Event(),))
                thread_2.start()
                
                thread_id_3 = exchange + '__' + base_asset + '-' + self.quote_asset
                self.stop_check_threads[thread_id_3] = False
                thread_3 = Thread(target=self.order_book_thread, args=(exchange, base_asset, self.quote_asset, Event(),))
                thread_3.start() 
            
        if not self.started:
            self.started = True  
            
    def execution(self, ch, method, properties, body):
        body_json = json.loads(body)
        order_book_time = body_json['time']
        exchange = body_json['exchange']
        base_asset = body_json['base_asset']
        quote_asset = body_json['quote_asset']
        data = body_json['data']
        pair: str = base_asset + '-' + quote_asset   
        base_asset_final = None
        if base_asset != self.strategy['pivot_asset']:
            base_asset_final = base_asset
        if pair not in self.order_books:
            self.order_books[pair] = {}     
        if data is not None and len(data) > 0:
            data['time'] = order_book_time
            self.order_books[pair][exchange] = data
        
        if base_asset_final is None:
            return
        
        if self.trade_time is not None and int(time.time() * 1e3) - (20 * 1000) < self.trade_time:
            return 
        
        for exchange in self.exchanges:
            pair_1 = base_asset_final + '-' + self.strategy['pivot_asset']
            pair_2 = self.strategy['pivot_asset'] + '-' + self.quote_asset
            pair_3 = base_asset_final + '-' + self.quote_asset
            if pair_1 not in self.order_books or pair_2 not in self.order_books or pair_3 not in self.order_books:
                continue
            if exchange not in self.order_books[pair_1] or len(self.order_books[pair_1][exchange]["asks"]) == 0 or len(self.order_books[pair_1][exchange]["bids"]) == 0 or self.order_books[pair_1][exchange]["time"] < int(time.time() * 1e3) - (60 * 1e3):
                continue
            if exchange not in self.order_books[pair_2] or len(self.order_books[pair_2][exchange]["asks"]) == 0 or len(self.order_books[pair_2][exchange]["bids"]) == 0 or self.order_books[pair_2][exchange]["time"] < int(time.time() * 1e3) - (60 * 1e3):
                continue
            if exchange not in self.order_books[pair_3] or len(self.order_books[pair_3][exchange]["asks"]) == 0 or len(self.order_books[pair_3][exchange]["bids"]) == 0 or self.order_books[pair_3][exchange]["time"] < int(time.time() * 1e3) - (60 * 1e3):
                continue
            
            VARIATIONS = {
                'base': [
                    {
                        'id': 'SELL-SELL-BUY',
                        'values': [
                            {
                                'pair': base_asset_final + '-' + self.strategy['pivot_asset'],
                                'tradeSide': TradeSide.SELL
                            },
                            {
                                'pair': self.strategy['pivot_asset'] + '-' + self.quote_asset,
                                'tradeSide': TradeSide.SELL
                            },
                            {
                                'pair': base_asset_final + '-' + self.quote_asset,
                                'tradeSide': TradeSide.BUY
                            }
                        ],
                    },
                    {
                        'id': 'SELL-BUY-BUY',
                        'values': [
                            {
                                'pair': base_asset_final + '-' + self.quote_asset,
                                'tradeSide': TradeSide.SELL
                            },
                            {
                                'pair': self.strategy['pivot_asset'] + '-' + self.quote_asset,
                                'tradeSide': TradeSide.BUY
                            },
                            {
                                'pair': base_asset_final + '-' + self.strategy['pivot_asset'],
                                'tradeSide': TradeSide.BUY
                            }
                        ],
                    }
                ],
                'quote': [
                    {
                        'id': 'BUY-SELL-SELL',
                        'values': [
                            {
                                'pair': base_asset_final + '-' + self.quote_asset,
                                'tradeSide': TradeSide.BUY
                            },
                            {
                                'pair': base_asset_final + '-' + self.strategy['pivot_asset'],
                                'tradeSide': TradeSide.SELL
                            },
                            {
                                'pair': self.strategy['pivot_asset'] + '-' + self.quote_asset,
                                'tradeSide': TradeSide.SELL
                            }
                        ],
                    },
                    {
                        'id': 'BUY-BUY-SELL',
                        'values': [
                            {
                                'pair': self.strategy['pivot_asset'] + '-' + self.quote_asset,
                                'tradeSide': TradeSide.BUY
                            },
                            {
                                'pair': base_asset_final + '-' + self.strategy['pivot_asset'],
                                'tradeSide': TradeSide.BUY
                            },
                            {
                                'pair': base_asset_final + '-' + self.quote_asset,
                                'tradeSide': TradeSide.SELL
                            }
                        ],
                    }
                ]
            }
                        
            for variation in VARIATIONS[self.strategy['target']]:
                
                if variation['id'] == 'BUY-BUY-SELL':
                    continue
                
                if self.strategy['target'] == 'base' and float(self.order_books[variation['values'][0]['pair']][exchange]['bids' if variation['values'][0]['tradeSide'] == TradeSide.SELL else 'asks'][0][1]) < DEPTHS[base_asset_final]['max']:
                    logging.info('-----------------------------------1 max depth is not reached %s %s', self.order_books[variation['values'][0]['pair']][exchange]['bids' if variation['values'][0]['tradeSide'] == TradeSide.SELL else 'asks'][0][1], DEPTHS[base_asset_final]["max"])
                    continue
                                                         
                if self.strategy['target'] == 'quote' and variation['values'][0]['pair'].split('-')[0] == base_asset_final and variation['values'][0]['pair'].split('-')[1] == self.quote_asset and float(self.order_books[variation['values'][0]['pair']][exchange]['bids' if variation['values'][0]['tradeSide'] == TradeSide.SELL else 'asks'][0][0]) * float(self.order_books[variation['values'][0]['pair']][exchange]['bids' if variation['values'][0]['tradeSide'] == TradeSide.SELL else 'asks'][0][1]) < DEPTHS[self.quote_asset]['max']:
                    logging.info('-----------------------------------1 max depth is not reached %s %s %s', self.quote_asset, str(float(self.order_books[variation['values'][0]['pair']][exchange]['bids' if variation['values'][0]['tradeSide'] == TradeSide.SELL else 'asks'][0][0]) * float(self.order_books[variation['values'][0]['pair']][exchange]['bids' if variation['values'][0]['tradeSide'] == TradeSide.SELL else 'asks'][0][1])), DEPTHS[self.quote_asset]["max"])
                    continue
                
                if self.strategy['target'] == 'quote' and variation['values'][0]['pair'].split('-')[0] == self.strategy['pivot_asset'] and variation['values'][0]['pair'].split('-')[1] == self.quote_asset and float(self.order_books[variation['values'][0]['pair']][exchange]['bids' if variation['values'][0]['tradeSide'] == TradeSide.SELL else 'asks'][0][0]) * float(self.order_books[variation['values'][0]['pair']][exchange]['bids' if variation['values'][0]['tradeSide'] == TradeSide.SELL else 'asks'][0][1]) < DEPTHS[self.quote_asset]['max']:
                    logging.info('-----------------------------------1 max depth is not reached %s %s %s', self.quote_asset, str(float(self.order_books[variation['values'][0]['pair']][exchange]['bids' if variation['values'][0]['tradeSide'] == TradeSide.SELL else 'asks'][0][0]) * float(self.order_books[variation['values'][0]['pair']][exchange]['bids' if variation['values'][0]['tradeSide'] == TradeSide.SELL else 'asks'][0][1])), DEPTHS[self.quote_asset]["max"])
                    continue
                                
                depth = DEPTHS[variation['values'][0]['pair'].split('-')[0]]['max']
                        
                price_1 = float(self.order_books[variation['values'][0]['pair']][exchange]['bids' if variation['values'][0]['tradeSide'] == TradeSide.SELL else 'asks'][0][0])
                price_2 = float(self.order_books[variation['values'][1]['pair']][exchange]['bids' if variation['values'][1]['tradeSide'] == TradeSide.SELL else 'asks'][0][0])
                price_3 = float(self.order_books[variation['values'][2]['pair']][exchange]['bids' if variation['values'][2]['tradeSide'] == TradeSide.SELL else 'asks'][0][0])
                                
                prices = [price_1, price_2, price_3]
                
                exchange_pair_1 = exchange + '__' + variation['values'][0]['pair']
                exchange_pair_2 = exchange + '__' + variation['values'][1]['pair']
                exchange_pair_3 = exchange + '__' + variation['values'][2]['pair']
                                        
                logging.info('first %s %s (%s) %s - %s (%s) %s - %s (%s) %s', exchange, 
                        variation['values'][0]['tradeSide'],
                        variation['values'][0]['pair'],
                        price_1, 
                        variation['values'][1]['tradeSide'],
                        variation['values'][1]['pair'],
                        price_2, 
                        variation['values'][2]['tradeSide'],
                        variation['values'][2]['pair'],
                        price_3,
                    )
                
                balances = asyncio.run(self.fetch_balances(exchanges=[exchange], base_asset=variation['values'][0]['pair'].split('-')[0]))
                if self.strategy['target'] == 'base' and balances[exchange][variation['values'][0]['pair'].split('-')[0]]['available'] * 0.98 < depth:
                    logging.info('-----------------------------------2 not enough balance of %s to sell in %s %s < %s', variation['values'][0]['pair'].split('-')[0], exchange, balances[exchange][variation['values'][0]['pair'].split('-')[0]]["available"] * 0.98, depth)
                    continue    
                if self.strategy['target'] == 'quote' and balances[exchange][variation['values'][0]['pair'].split('-')[1]]['available'] * 0.98 < depth * price_1:
                    logging.info('-----------------------------------2 not enough balance of %s to buy in %s %s < %s', variation['values'][0]['pair'].split('-')[1], exchange, balances[exchange][variation['values'][0]['pair'].split('-')[1]]["available"] * 0.98, depth * price_1)
                    continue     
                                                                
                profitability = 0
                bid_avg_price = None        
                ask_avg_price = None
                 
                if variation['id'] == 'SELL-SELL-BUY':
                    bid_avg_price = price_1 * price_2
                    ask_avg_price = price_3
                    arb_opportunity = bid_avg_price - ask_avg_price
                    profitability = (arb_opportunity * 100 / ask_avg_price) - (self.commons[exchange_pair_1].sell_fee_percentage + self.commons[exchange_pair_2].sell_fee_percentage + self.commons[exchange_pair_3].buy_fee_percentage)
                elif variation['id'] == 'SELL-BUY-BUY':
                    bid_avg_price = price_1
                    ask_avg_price = price_2 * price_3
                    arb_opportunity = bid_avg_price - ask_avg_price
                    profitability = (arb_opportunity * 100 / ask_avg_price) - (self.commons[exchange_pair_1].sell_fee_percentage + self.commons[exchange_pair_2].buy_fee_percentage + self.commons[exchange_pair_3].buy_fee_percentage)
                elif variation['id'] == 'BUY-SELL-SELL':
                    bid_avg_price = price_2 * price_3
                    ask_avg_price = price_1
                    arb_opportunity = bid_avg_price - ask_avg_price
                    profitability = (arb_opportunity * 100 / ask_avg_price) - (self.commons[exchange_pair_1].buy_fee_percentage + self.commons[exchange_pair_2].sell_fee_percentage + self.commons[exchange_pair_3].sell_fee_percentage)
                elif variation['id'] == 'BUY-BUY-SELL':
                    bid_avg_price = price_3
                    ask_avg_price = price_1 * price_2
                    arb_opportunity = bid_avg_price - ask_avg_price
                    profitability = (arb_opportunity * 100 / ask_avg_price) - (self.commons[exchange_pair_1].buy_fee_percentage + self.commons[exchange_pair_2].buy_fee_percentage + self.commons[exchange_pair_3].sell_fee_percentage)
          
                if profitability < self.strategy['min_profitability']:
                    logging.info('-----------------------------------3 min profitability is not reached %s - %s %s %s -> %s %s', variation['id'], exchange_pair_1, exchange_pair_2, exchange_pair_3, profitability, self.strategy["min_profitability"])
                    continue     
                             
                if self.trade_time is not None and int(time.time() * 1000) - (20 * 1000) < self.trade_time:
                    continue
                self.trade_time = int(time.time() * 1000)
                                            
                amount_to_sustract = None
                amount_to_add = None
                asset_to_sustract = None
                asset_to_add = None
                amount = None
                logging.info('-------------------profitability------------------- %s -> %s %s %s %s', variation['id'], profitability, price_1, price_2, price_3) 
                i = 0
                for value in variation['values']:
                            
                    if not self.testing:
                        print('CREATE trades')
                            
                    elif self.emulated_balance is not None:
                        price = prices[i]
                        logging.info('-------------------price------------------- %s -> %s %s', i, price, int(time.time() * 1e3))
                        i += 1
                        exchange_pair = exchange + '__' + value['pair']
                        if value['tradeSide'] == TradeSide.SELL:
                            if amount is None:
                                amount = depth
                            else:
                                amount = amount_to_add
                            fee_cost = (amount * price) * (self.commons[exchange_pair].sell_fee_percentage / 100)
                            fee_asset = value['pair'].split('-')[1]
                                    
                            amount_to_sustract = amount
                            amount_to_add = (amount * price) - fee_cost 
                            asset_to_sustract = value['pair'].split('-')[0]
                            asset_to_add = value['pair'].split('-')[1]
                                    
                        elif value['tradeSide'] == TradeSide.BUY:
                            if amount is None:
                                amount = depth
                            else:
                                amount = amount_to_add / price
                            fee_cost = (amount * price) * (self.commons[exchange_pair].buy_fee_percentage / 100)
                            fee_asset = value['pair'].split('-')[1]
                                    
                            amount_to_sustract = amount * price
                            amount_to_add = amount - (fee_cost / price)
                            asset_to_sustract = value['pair'].split('-')[1]
                            asset_to_add = value['pair'].split('-')[0]
                                    
                            if self.commons[exchange_pair].buy_fee_asset_type == 'base':        
                                fee_cost = amount * (self.commons[exchange_pair].buy_fee_percentage / 100)
                                fee_asset = value['pair'].split('-')[0]
                                amount_to_sustract = amount * price
                                amount_to_add = amount - fee_cost 

                        trade = Trade(bot_id=self.bot_id, strategy_id=self.strategy['id'], base_asset=value['pair'].split('-')[0], quote_asset=value['pair'].split('-')[1], timestamp=self.trade_time, order_id='', side=value['tradeSide'], price=price, amount=amount, fee={"cost": fee_cost, "currency": fee_asset}, exchange_id='', exchange=exchange)
                        logging.info('-------------------trade------------------- %s', trade)    
                        asyncio.run(self.bot_db.create_trade_db(trade=trade))

                        logging.info('-------------------execute_emulated_balance------------------- %s - add -> %s (%s) - sustract -> %s (%s)', exchange, 
                                    amount_to_add, 
                                    asset_to_add,
                                    amount_to_sustract, 
                                    asset_to_sustract
                                )
                                
                        asyncio.run(execute_emulated_balance_new(
                                name=self.emulated_balance, 
                                exchange=exchange,
                                asset=asset_to_sustract,
                                amount=amount_to_sustract,
                                asset_turn=asset_to_add,
                                amount_turn=amount_to_add,
                                operation='trade'
                            ))
                        
    async def fetch_balances(self, exchanges: list[str], base_asset):
        if self.testing and self.emulated_balance is not None:
            balances = await fetch_emulated_balance_new(name=self.emulated_balance)
            return balances[0]['current']
        else:
            balances: dict = {}
            for exchange in exchanges:
                balances[exchange] = await self.execute(exchange=exchange, base_asset=base_asset, quote_asset=self.quote_asset, name='fetch_balance', attributes=())
            return balances
                                    

DEPTHS = {
    'USDT': {
        'min': 500,
        'max': 2000
    },
    'MX': {
        'min': 200,
        'max': 800
    },
    'BTC': {
        'min': 0.01,
        'max': 0.04
    },
    'ETH': {
        'min': 0.1,
        'max': 0.4
    },
    'SOL': {
        'min': 1,
        'max': 4
    },
    'ADA': {
        'min': 1000,
        'max': 4000
    },
    'BNB': {
        'min': 1,
        'max': 4
    },
    'DOGE': {
        'min': 3000,
        'max': 12000
    },
}